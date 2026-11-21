# -*- coding: utf-8 -*-
"""HWPX 문서의 글자를 바꾼다. 서식, 표, 그림은 그대로 두고 글자만 고친다. 한컴오피스가 없어도 된다.

    python hwpx_replace.py in.hwpx out.hwpx --map 바꿀말.tsv            # 한 줄에 '찾을 말<TAB>바꿀 말'
    python hwpx_replace.py in.hwpx out.hwpx --pair "·" "와 " --pair "—" ", "
    python hwpx_replace.py in.hwpx out.hwpx --map 바꿀말.tsv --dry-run  # 몇 군데가 바뀌는지만 봄

.hwp 문서는 먼저 hwp_convert.py로 .hwpx로 바꾼 뒤 고치고, 다시 .hwp로 바꾼다.
    python hwp_convert.py 기획안.hwp 기획안.hwpx
    python hwpx_replace.py 기획안.hwpx 기획안_고침.hwpx --map 바꿀말.tsv
    python hwp_convert.py 기획안_고침.hwpx 기획안_고침.hwp

동작
- Contents/section*.xml의 <hp:t> 글자(와 그 안 <hp:tab/> 등의 뒤 글자)에서 찾아 바꿈. --equations를 주면 수식 스크립트도 바꿈
- 바뀐 문단의 <hp:linesegarray>(한글이 저장해 둔 줄 나눔 정보)를 지워 한글이 줄을 다시 나누게 함
- zip 안 파일 순서와 압축 방식을 원본 그대로 유지함 (mimetype이 맨 앞, 무압축)
한계: 한 낱말이 서식 때문에 <hp:t> 여러 개로 나뉘어 있으면 찾지 못한다. 찾지 못한 항목은 끝에 따로 알려 준다.
글자를 늘리면 줄과 쪽이 밀릴 수 있으니, 바꾼 뒤 PDF로 내보내 쪽 나눔을 확인한다.
"""
import argparse
import re
import sys
import zipfile

from lxml import etree

HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'


def load_pairs(a):
    pairs = [tuple(p) for p in (a.pair or [])]
    if a.map:
        with open(a.map, encoding='utf-8-sig') as f:
            for line in f:
                line = line.rstrip('\r\n')
                if not line or line.startswith('#'):
                    continue
                old, _, new = line.partition('\t')
                pairs.append((old, new))
    if not pairs:
        raise SystemExit('바꿀 말이 없음: --map 파일이나 --pair를 주세요')
    return pairs


def replace_in(el_text, pairs, hits):
    for i, (old, new) in enumerate(pairs):
        if old and old in el_text:
            hits[i] += el_text.count(old)
            el_text = el_text.replace(old, new)
    return el_text


def edit_section(xml, pairs, hits, equations, all_lineseg):
    root = etree.fromstring(xml)
    touched = set()
    for t in root.iter(HP + 't'):
        before = hits[:]
        if t.text:
            t.text = replace_in(t.text, pairs, hits)
        for ch in t:
            if ch.tail:
                ch.tail = replace_in(ch.tail, pairs, hits)
        if hits != before:
            p = next((a for a in t.iterancestors(HP + 'p')), None)
            if p is not None:
                touched.add(p)
    if equations:
        for s in root.iter(HP + 'script'):
            before = hits[:]
            if s.text:
                s.text = replace_in(s.text, pairs, hits)
            if hits != before:
                p = next((a for a in s.iterancestors(HP + 'p')), None)
                if p is not None:
                    touched.add(p)
    targets = root.iter(HP + 'p') if all_lineseg else touched
    dropped = 0
    for p in list(targets):
        for ls in p.findall(HP + 'linesegarray'):
            p.remove(ls)
            dropped += 1
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True), len(touched), dropped


def main():
    ap = argparse.ArgumentParser(description='HWPX 글자 바꾸기 (서식 유지)')
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--map', help="'찾을 말<TAB>바꿀 말' 줄로 된 UTF-8 파일")
    ap.add_argument('--pair', nargs=2, action='append', metavar=('OLD', 'NEW'))
    ap.add_argument('--equations', action='store_true', help='수식 스크립트(<hp:script>)도 바꿈')
    ap.add_argument('--all-lineseg', action='store_true', help='모든 문단의 줄 나눔 정보를 지움 (구조를 크게 바꿨을 때)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    pairs = load_pairs(a)
    hits = [0] * len(pairs)
    paras = dropped = 0
    with zipfile.ZipFile(a.src) as zin:
        infos = zin.infolist()
        data = {}
        for info in infos:
            raw = zin.read(info.filename)
            if re.fullmatch(r'Contents/section\d+\.xml', info.filename):
                raw, n, d = edit_section(raw, pairs, hits, a.equations, a.all_lineseg)
                paras += n
                dropped += d
            data[info.filename] = raw
    for (old, new), h in zip(pairs, hits):
        print('%4d곳  %r -> %r' % (h, old, new))
    print('바뀐 문단 %d개, 지운 줄 나눔 정보 %d개' % (paras, dropped))
    missing = [old for (old, _), h in zip(pairs, hits) if h == 0]
    if missing:
        print('찾지 못함 %d개 (서식 때문에 글자가 나뉘었거나 없는 말): %s' % (len(missing), ', '.join(map(repr, missing[:10]))))
    if a.dry_run:
        return
    with zipfile.ZipFile(a.dst, 'w') as zout:
        for info in infos:
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            zi.external_attr = info.external_attr
            zout.writestr(zi, data[info.filename])
    print('저장', a.dst)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
