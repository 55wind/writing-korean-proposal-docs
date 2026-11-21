# -*- coding: utf-8 -*-
"""예시 기획안(가상의 '동네 공공시설 예약 도우미')을 Word(.docx)로 만든다.

    python examples/example_diagrams.py        # 그림 SVG 먼저
    python examples/example_build_docx.py      # -> examples/out/example_proposal.docx
    python scripts/word_to_pdf.py examples/out/example_proposal.docx --embed-fonts --pages 4

SKILL.md의 규칙을 그대로 코드로 옮긴 예시다.
- 글씨는 검정 한 가지, 크기는 본문과 표 두 가지. 강조는 굵게만 함
- 문장 문단은 첫 줄 한 글자(3.5mm) 들여쓰기, 목록은 Word 글머리표
- 표: 세로 가운데 정렬, 위와 머리글 아래와 맨 아래는 굵은 검정 선, 칸 사이는 연회색 가는 선
- 캡션: Word 캡션 기능(SEQ 필드). 그림은 아래 가운데 '(그림 n)', 표는 왼쪽 위 '<표 n>'
- 그림: SVG를 넣고 PNG는 SVG를 못 읽는 프로그램용 대체 이미지로만 씀
글꼴은 Pretendard(Regular, SemiBold, Bold, TTF판)가 설치돼 있어야 PDF에서 모양이 맞는다.
"""
import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, '..', 'scripts')
sys.path.insert(0, SCRIPTS)
from docx import Document  # noqa: E402
from docx.enum.style import WD_STYLE_TYPE  # noqa: E402
from docx.shared import Mm  # noqa: E402
from docx_helpers import *  # noqa: E402,F401,F403

OUT_DIR = os.path.join(HERE, 'out')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT_DIR, 'example_proposal.docx')

# ---------------- 쪽과 글자 크기 ----------------
MARGIN_X = 15.0
TW = 210 - 2 * MARGIN_X  # 본문 폭 (mm)
BODY, BODY_L = 9.0, 14.4  # 본문 크기와 줄 간격 (pt)
TT, TT_L = 7.9, 11.6      # 표 글자
SCALE['size'] = 1.12      # 글자 전체 배율. 쪽수를 맞출 때 여기만 바꿈
SCALE['line'] = 1.09

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.top_margin, sec.bottom_margin = Mm(15), Mm(12.5)
sec.left_margin = sec.right_margin = Mm(MARGIN_X)
sec.header_distance, sec.footer_distance = Mm(6.6), Mm(5.6)

# Word 2013 이후 호환 모드, 동아시아 언어는 한국어
settings = doc.settings.element
for cs in settings.iter(qn('w:compatSetting')):
    if cs.get(qn('w:name')) == 'compatibilityMode':
        cs.set(qn('w:val'), '15')
tfl = settings.find(qn('w:themeFontLang'))
if tfl is not None:
    tfl.set(qn('w:eastAsia'), 'ko-KR')

styles = doc.styles
rpr_default = styles.element.find(qn('w:docDefaults')).find(qn('w:rPrDefault')).find(qn('w:rPr'))
set_rfonts(rpr_default)
lang = child(rpr_default, 'w:lang', RPR)
lang.set(qn('w:val'), 'en-US')
lang.set(qn('w:eastAsia'), 'ko-KR')
pp = styles.element.find(qn('w:docDefaults')).find(qn('w:pPrDefault')).find(qn('w:pPr'))
if pp is not None and pp.find(qn('w:spacing')) is not None:
    pp.remove(pp.find(qn('w:spacing')))


def setup_style(st, size=None, bold=None, color=None, line=None, before=0, after=0, **pf):
    pPr = st.element.get_or_add_pPr()
    rPr = st.element.get_or_add_rPr()
    set_rfonts(rPr)
    rfmt(rPr, size=size, bold=bold, color=color, italic=False)
    pfmt(pPr, line=line, before=before, after=after, **pf)
    child(pPr, 'w:autoSpaceDE', PPR, {'w:val': '0'})
    child(pPr, 'w:autoSpaceDN', PPR, {'w:val': '0'})
    for el in rPr.findall(qn('w:color')):
        for a in list(el.attrib):
            if a != qn('w:val'):
                del el.attrib[a]
    return st


def add_style(name, base='Normal', **kw):
    st = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = styles[base]
    st.quick_style = True
    return setup_style(st, **kw)


normal = setup_style(styles['Normal'], size=BODY, color=C['ink'], line=BODY_L)
child(normal.element.get_or_add_pPr(), 'w:wordWrap', PPR, {'w:val': '1'})
rfmt(normal.element.get_or_add_rPr(), spacing=-0.1)
add_style('Table Text', size=TT, color=C['ink'], line=TT_L)
setup_style(styles['Caption'], size=BODY, color=C['ink'], bold=False, line=BODY_L, before=mm2pt(1.2))
setup_style(styles['Heading 1'], size=14.5, bold=True, color=C['ink'], line=21, before=0, after=mm2pt(3.2),
            keep_next=True, keep_lines=True, pbb=True, bdr={'bottom': (1.5, C['ink'], 4)}, outline=0)
setup_style(styles['Heading 2'], size=10.6, bold=True, color=C['ink'], line=15, before=mm2pt(4.2),
            after=mm2pt(1.8), keep_next=True, keep_lines=True, outline=1)
for name in ('Header', 'Footer'):
    st = setup_style(styles[name], size=6.8, color=C['faint'], line=10)
    for t_ in st.element.pPr.findall(qn('w:tabs')):
        st.element.pPr.remove(t_)

core = doc.core_properties
core.title = '동네 공공시설 예약 도우미 기획안 (예시)'
core.author = core.last_modified_by = '작성자'
core.created = core.modified = datetime.datetime(2026, 1, 1, 9, 0, 0)

# 머리글: 왼쪽 공모전 이름, 오른쪽 지금 장 제목(STYLEREF). 바닥글: 문서 이름과 쪽 번호
hp = sec.header.paragraphs[0]
hp.style = styles['Header']
pfmt(hp, tabs=[(TW, 'right')], bdr={'bottom': (0.5, C['line'], 3)})
runs(hp, '2026 OO 아이디어 공모전 (예시)\t')
field(hp, 'STYLEREF 1 \\* MERGEFORMAT', '아이디어 기획안', bold=True, color=C['blue'])
fp = sec.footer.paragraphs[0]
fp.style = styles['Footer']
pfmt(fp, tabs=[(TW, 'right')])
runs(fp, '동네 공공시설 예약 도우미 기획안\t')
field(fp, 'PAGE', '1', bold=True, color=C['ink'])
runs(fp, ' / ', bold=True, color=C['ink'])
field(fp, 'NUMPAGES', '3', bold=True, color=C['ink'])

# ---------------- 부품 ----------------
LINE = (0.5, C['line'])       # 칸 사이 연회색 가는 선
INK_TOP = (1.25, C['ink'])    # 표 위, 머리글 아래, 맨 아래 굵은 검정 선
FIRST = 3.5                   # 문장 문단 첫 줄 들여쓰기 (mm, 약 한 글자)


def H1(num, title, first=False):
    p = doc.add_paragraph(style='Heading 1')
    if first:
        pfmt(p, pbb=False)
    runs(p, num + '.', color=C['blue'])
    runs(p, ' ' + title)
    return p


def H2(num, title):
    p = doc.add_paragraph(style='Heading 2')
    runs(p, num, color=C['blue'])
    runs(p, '  ' + title)
    return p


def body(markup, **pf):
    kw = dict(after=mm2pt(1.6), first=FIRST)
    kw.update(pf)
    return para(doc, markup, **kw)


def dtable(widths, head, rows, th=True, size=TT, line=TT_L, head_hl=(), mar=(1.3, 1.8, 1.3, 1.8)):
    """데이터 표. 첫 열은 항목 칸(연회색, 가운데). head_hl의 열은 머리글을 파란 바탕 흰 글씨로 강조.
    rows의 칸은 문자열 또는 dict(t=글, c=가운데 정렬 여부, hl=연한 파란 바탕)"""
    n = len(rows) + (1 if head else 0)
    t = table(doc, n, widths, borders={'top': INK_TOP, 'bottom': INK_TOP, 'insideH': LINE, 'insideV': LINE}, mar=mar)
    ri = 0
    if head:
        r = t.rows[0]
        row(r, header=True)  # 쪽이 넘어가면 머리글 행 반복
        for i, (c, txt) in enumerate(zip(r.cells, head)):
            hl = i in head_hl
            cell(c, shade=C['blue'] if hl else C['ground'], borders={'bottom': INK_TOP}, valign='center')
            fill(c, txt, align='center', line=line, run=dict(bold=True, color=C['white'] if hl else C['ink'], size=size))
        ri = 1
    for data in rows:
        r = t.rows[ri]
        row(r)  # 행이 쪽 사이에서 잘리지 않음
        under_head = head and ri == 1
        ri += 1
        for i, (c, spec) in enumerate(zip(r.cells, data)):
            if isinstance(spec, str):
                spec = dict(t=spec)
            is_th = th and i == 0
            shade = C['ground'] if is_th else (C['wash'] if spec.get('hl') else None)
            # 머리글 아래 굵은 선은 머리글 칸 아래와 첫 데이터 행 칸 위에 함께 넣음
            cell(c, shade=shade, borders={'top': INK_TOP} if under_head else None, valign='center')
            run = dict(size=size)
            if is_th:
                run.update(bold=True, color=C['ink'])
            fill(c, spec['t'], line=line, align='center' if (spec.get('c') or is_th) else None, run=run)
    return t


BULLET_NUM = 90


def setup_bullets():
    """Word 글머리표 목록 정의 (파란 점, 왼쪽 6.5mm 들여쓰기, 내어쓰기 3.5mm)"""
    numbering = doc.part.numbering_part.element
    absn = parse_xml(
        '<w:abstractNum %s w:abstractNumId="%d"><w:multiLevelType w:val="singleLevel"/>'
        '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/>'
        '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="%d" w:hanging="%d"/></w:pPr>'
        '<w:rPr><w:rFonts w:ascii="Pretendard" w:hAnsi="Pretendard" w:eastAsia="Pretendard" w:cs="Pretendard"/>'
        '<w:b/><w:color w:val="3F58D4"/></w:rPr></w:lvl></w:abstractNum>'
        % (nsdecls('w'), BULLET_NUM, tw(6.5), tw(3.5)))
    first_num = numbering.find(qn('w:num'))
    if first_num is not None:
        first_num.addprevious(absn)
    else:
        numbering.append(absn)
    numbering.append(parse_xml('<w:num %s w:numId="%d"><w:abstractNumId w:val="%d"/></w:num>'
                               % (nsdecls('w'), BULLET_NUM, BULLET_NUM)))


def points(items):
    """글머리표 목록. 항목마다 굵은 첫 문장으로 시작"""
    for i, txt in enumerate(items):
        p = para(doc, txt, after=mm2pt(1.2) if i < len(items) - 1 else mm2pt(1.6), line=BODY_L)
        num = child(p._p.get_or_add_pPr(), 'w:numPr', PPR)
        child(num, 'w:ilvl', ['w:ilvl', 'w:numId'], {'w:val': 0})
        child(num, 'w:numId', ['w:ilvl', 'w:numId'], {'w:val': BULLET_NUM})


def diagram(name, alt):
    """out/<name>.svg를 문서 폭에 맞춰 넣음. PNG가 없으면 svg_to_png.py로 만듦"""
    svg, png = os.path.join(OUT_DIR, name + '.svg'), os.path.join(OUT_DIR, name + '.png')
    if not os.path.exists(png):
        subprocess.run([sys.executable, os.path.join(SCRIPTS, 'svg_to_png.py'), svg, png, '--width', '1800'],
                       check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    p = doc.add_paragraph()
    pfmt(p, auto_line=1.0, before=0, after=0, keep_next=True)
    picture_svg(p, png, svg, TW, doc.part, alt=alt)
    return p


setup_bullets()

# =====================================================================
# 1. 아이디어 개요
# =====================================================================
H1('1', '아이디어 개요', first=True)
H2('1.1', '배경과 문제')
body('구민 체육관, 회의실, 강당 같은 공공시설은 구청과 시설마다 예약 사이트가 달라 원하는 시간에 쓸 수 있는 곳을 '
     '한 번에 찾기 어려움. 이용 조건(대상, 인원, 요금)도 시설마다 글로 적혀 있어 하나하나 읽어 봐야 함.')
points([
    '<b>흩어진 예약 사이트.</b> 한 구에만 예약 사이트가 3개 이상이고, 시설을 비교하려면 사이트를 오가야 함',
    '<b>글로만 된 이용 조건.</b> "관내 거주자 우선", "10인 이상" 같은 조건을 이용자가 직접 읽고 판단해야 함',
    '<b>창구 문의 집중.</b> 예약 가능 여부를 묻는 전화와 방문 문의가 창구 업무의 큰 몫을 차지함',
])
H2('1.2', '해결 방법')
body('이용자가 원하는 것을 한 문장으로 적으면 AI가 날짜, 인원, 거리 같은 조건을 뽑고, 예약 가능 여부와 요금은 규칙 엔진이 '
     '계산함. AI는 글을 다루고, 숫자는 규칙으로 계산해 틀린 숫자가 화면에 나오지 않게 함.')

tab = caption(doc, '표', '지금 방식과 제안 방식 비교')
dtable([30, 75, 75], ['구분', '지금 방식', '제안 방식'], [
    ['시설 찾기', '구청과 시설별 사이트를 하나씩 확인', '한 문장 입력으로 여러 시설을 한 번에 비교'],
    ['조건 확인', '이용 조건 글을 직접 읽고 판단', 'AI가 조건을 뽑고 원문 구절을 함께 보여 줌'],
    ['예약 가능 여부', '사이트마다 달력을 열어 확인', dict(t='규칙 엔진이 빈 시간과 요금을 계산', hl=True)],
    ['걸리는 시간', '10분 이상', dict(t='약 3분', c=True, hl=True)],
], head_hl=(2,))

# =====================================================================
# 2. 시스템 구성
# =====================================================================
H1('2', '시스템 구성')
H2('2.1', '시스템 아키텍처')
body('이용자 화면, 서버, 생성형 AI, 데이터의 네 층으로 나눔. 생성형 AI는 조건 추출과 안내문 작성만 맡고, 예약 가능 시간과 '
     '요금은 브라우저 안의 규칙 엔진이 계산함. AI가 만든 문장은 검증기가 숫자와 시설 이름을 원문과 대조한 뒤에만 화면에 보냄.')
diagram('architecture', '시스템 아키텍처')
caption(doc, '그림', '시스템 아키텍처')

tab = caption(doc, '표', '구성 요소별 역할')
dtable([34, 26, 120], ['구성 요소', '종류', '하는 일'], [
    ['조건 추출', dict(t='생성형 AI', c=True), '이용자가 적은 문장에서 날짜, 인원, 지역, 시설 종류를 뽑음'],
    ['규칙 엔진', dict(t='규칙', c=True), '정리된 이용 조건과 빈 시간을 대조해 예약 가능 여부와 요금을 계산함'],
    ['검증기', dict(t='규칙', c=True), 'AI가 만든 안내문의 숫자, 시설 이름, 원문 구절을 정리된 정보와 대조함'],
    ['일괄 정리', dict(t='생성형 AI', c=True), '공공데이터의 이용 조건 글을 항목(대상, 인원, 요금)으로 미리 정리함'],
])

H2('2.2', '서비스 흐름')
body('예시 인물이 휴대폰으로 시설을 찾아 예약 사이트로 가기까지 약 3분이 걸림. 타이핑은 원하는 것을 적는 한 번뿐이고, '
     '나머지 단계는 고르거나 확인만 함.')
diagram('service-flow', '서비스 흐름')
caption(doc, '그림', '서비스 흐름: 예시 인물의 3분 여정')

# =====================================================================
# 3. 추진 일정
# =====================================================================
H1('3', '추진 일정')
body('공모전 기간 안에 모의데이터로 화면과 규칙 엔진을 먼저 만들고, 선정 뒤에 실제 공공데이터 API를 연결함.')
tab = caption(doc, '표', '추진 일정')
dtable([30, 30, 120], ['단계', '기간', '내용'], [
    ['1단계', dict(t='1~2주', c=True), '모의데이터로 화면, 조건 추출, 규칙 엔진 만들기'],
    ['2단계', dict(t='3~4주', c=True), '검증기 붙이기, 예시 인물로 3분 여정 시험'],
    ['3단계', dict(t='선정 뒤', c=True), dict(t='공공데이터 API 연결, 창구 직원과 함께 쓰는 화면 시험', hl=True)],
])

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
doc.save(OUT)
print('saved', os.path.abspath(OUT))
