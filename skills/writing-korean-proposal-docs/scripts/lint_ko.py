# -*- coding: utf-8 -*-
"""제출 문서 규칙 검사기. 한글(.hwp, .hwpx), Word(.docx), PDF, 텍스트 파일 모두 된다. 한컴오피스나 Word가 없어도 된다.

    python lint_ko.py 기획안.hwp
    python lint_ko.py 기획안.docx --rules punct,tone
    python lint_ko.py 기획안.hwpx --allow "·"          # 이 문서에서는 가운데점을 허용

검사 항목 (--rules로 고름, 기본은 전부)
- punct   : 엠대시(—), 엔대시(–), 가운데점(·, ㆍ), 원문자(①, ❶ 등)
- space   : en space, em space 같은 특수 공백. Word에서는 Cambria Math 글꼴이 섞이는 원인
- tone    : '~음, ~함, ~임'이 아닌 문장 끝 ('~합니다', '~해요', '~했다' 등). 따옴표 안은 건너뜀
- caption : '[표 1]', '그림 1.', 'Figure 1' 같은 캡션. '<표 1> 제목', '(그림 1) 제목' 형식을 권함
- mention : 본문에서 표를 '표 3'처럼 부른 곳. '<표 3>'으로 부르기를 권함 (기본 꺼짐, --rules에 넣으면 켜짐)

찾은 것이 있으면 종료 코드 1을 돌려준다. 문서를 고치지는 않는다.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hwp_text import paragraphs  # noqa: E402

PUNCT = {'—': '엠대시', '–': '엔대시', '·': '가운데점', 'ㆍ': '가운데점(한글 아래아)', '‧': '가운데점'}
CIRCLED = re.compile('[①-⑳❶-❿➀-➓⓫-⓴㉑-㉟㊱-㊿]')
SPACES = {' ': 'en space', ' ': 'em space', ' ': 'thin space', '​': '폭 없는 공백',
          '　': '전각 공백', ' ': 'figure space'}
QUOTED = re.compile(r'"[^"]*"|“[^”]*”|‘[^’]*’|「[^」]*」|『[^』]*』|\'[^\']*\'')
# 문장 끝: 마침표 앞 마지막 어절. 개조식(~음/~함/~임/~됨 등)이 아닌 끝을 잡음
BAD_END = re.compile(r'(습니다|합니다|입니다|됩니다|니다|어요|아요|여요|해요|에요|예요|세요|군요|네요|죠|이다|했다|한다|된다|있다|없다|였다|았다|었다|겠다|는다|ㄴ다)[.!?]?\s*$')
CAPTION_BAD = re.compile(r'^\s*(\[\s*(표|그림)\s*\d+\s*\]|(표|그림)\s*\d+\s*[.:]|<\s*그림\s*\d+\s*>|\(\s*표\s*\d+\s*\)|'
                         r'(Table|Figure|Fig\.)\s*\d+)')
MENTION = re.compile(r'(?<![<\w])표\s*\d+(?!\s*>)')


def sentences(text):
    """마침표 기준으로 자르되, 숫자 사이 마침표(3.5)는 자르지 않음"""
    parts = re.split(r'(?<=[.!?])(?!\d)\s+', text.strip())
    return [p for p in parts if p]


def check(path, rules, allow):
    found = []
    for where, text in paragraphs(path):
        if not text.strip() or text.startswith('[EQ]'):
            continue
        short = text.strip()
        ctx = short if len(short) <= 70 else short[:67] + '...'
        if 'punct' in rules:
            for ch, name in PUNCT.items():
                if ch in text and ch not in allow:
                    found.append(('문장부호', where, '%s(%s) %d개' % (name, ch, text.count(ch)), ctx))
            m = CIRCLED.findall(text)
            if m and not set(m) <= set(allow):
                found.append(('문장부호', where, '원문자 %s' % ''.join(sorted(set(m))), ctx))
        if 'space' in rules:
            for ch, name in SPACES.items():
                if ch in text and ch not in allow:
                    found.append(('특수 공백', where, '%s %d개' % (name, text.count(ch)), ctx))
        if 'tone' in rules:
            body = QUOTED.sub('""', text)
            for s in sentences(body):
                if BAD_END.search(s):
                    end = s.strip()[-14:]
                    found.append(('말투', where, "'...%s' 대신 '~음, ~함, ~임'으로" % end, ctx))
        if 'caption' in rules and CAPTION_BAD.match(text):
            found.append(('캡션', where, "'<표 N> 제목' 또는 '(그림 N) 제목' 형식으로", ctx))
        if 'mention' in rules and not CAPTION_BAD.match(text):
            for m in MENTION.finditer(QUOTED.sub('""', text)):
                found.append(('표 부르기', where, "'%s' 대신 '<%s>'" % (m.group(), m.group()), ctx))
    return found


def main():
    ap = argparse.ArgumentParser(description='한국어 제출 문서 규칙 검사 (hwp, hwpx, docx, pdf, txt)')
    ap.add_argument('path')
    ap.add_argument('--rules', default='punct,space,tone,caption', help='punct,space,tone,caption,mention 중 쉼표로')
    ap.add_argument('--allow', default='', help='허용할 글자들 (예: "·")')
    ap.add_argument('--max', type=int, default=200, help='출력할 최대 개수')
    a = ap.parse_args()
    rules = set(a.rules.split(','))
    found = check(a.path, rules, set(a.allow))
    for kind, where, what, ctx in found[:a.max]:
        print('[%s] %s : %s\n    %s' % (kind, where, what, ctx))
    counts = {}
    for f in found:
        counts[f[0]] = counts.get(f[0], 0) + 1
    print('\n%s : %s' % (os.path.basename(a.path),
                          ', '.join('%s %d건' % kv for kv in counts.items()) if counts else '규칙 위반 없음'))
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
