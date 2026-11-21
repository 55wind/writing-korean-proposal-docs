# -*- coding: utf-8 -*-
"""README의 '작동 방식' 그림을 이 스킬의 svgdiagram으로 그린다 (한국어판과 영어판).

    python assets/make_how_it_works.py
      -> assets/how-it-works.svg, assets/how-it-works.png
      -> assets/how-it-works-en.svg, assets/how-it-works-en.png
"""
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, '..', 'skills', 'writing-korean-proposal-docs', 'scripts')
sys.path.insert(0, SCRIPTS)
import svgdiagram as sd  # noqa: E402

sd.ICON_DIR = os.path.join(HERE, '_icons')
C = sd.C
ICONS = ['rules', 'gallery', 'flow_chart', 'binoculars', 'document', 'print', 'ruler', 'file', 'redo']
os.makedirs(sd.ICON_DIR, exist_ok=True)
for n in ICONS:
    p = os.path.join(sd.ICON_DIR, n + '.svg')
    if not os.path.exists(p):
        req = urllib.request.Request('https://cdn.jsdelivr.net/npm/flat-color-icons@1.1.0/svg/%s.svg' % n,
                                     headers={'User-Agent': 'icons-fetch'})
        with open(p, 'wb') as f:
            f.write(urllib.request.urlopen(req, timeout=30).read())

TEXT = {
    'ko': dict(
        band=('SKILL.md 규칙', 'Claude가 말투, 문장부호, 표, 캡션, 그림 규칙을 먼저 읽고 Word와 한글(HWP) 문서 모두에 적용'),
        steps=[
            ('gallery', '아이콘 고르기', 'fetch_icons8.py', ['무료 아이콘 329개 중', '후보 시트로 고르기'], '_sheet.png'),
            ('flow_chart', '그림 그리기', 'svgdiagram.py', ['계층 칸, 아이콘 노드,', '라벨 화살표 배치'], 'figure.svg'),
            ('binoculars', 'PNG로 확인', 'svg_to_png.py', ['Claude가 직접 보고', '겹침과 잘림 찾기'], 'figure.png'),
            ('document', 'Word 만들기', 'docx_helpers.py', ['스타일, 표, 글머리표,', '캡션 필드, SVG 그림'], 'proposal.docx'),
            ('print', '내보내기', 'word_to_pdf.py', ['hwp_convert.py로', 'HWP, HWPX, PDF'], '.pdf  .hwp'),
            ('ruler', '점검', 'pdf_check.py', ['lint_ko.py로 말투,', '문장부호, 캡션까지'], '점검 결과'),
        ],
        loops=('겹침, 잘림 고치기', '쪽이 넘치면 줄일 곳을 정하고 다시'),
        out='how-it-works'),
    'en': dict(
        band=('SKILL.md rules', 'Claude reads the tone, punctuation, table, caption and figure rules first, then applies them to Word and HWP files'),
        steps=[
            ('gallery', 'Pick icons', 'fetch_icons8.py', ['329 free icons,', 'choose from a sheet'], '_sheet.png'),
            ('flow_chart', 'Draw figures', 'svgdiagram.py', ['Tiers, icon nodes,', 'labeled arrows'], 'figure.svg'),
            ('binoculars', 'Check as PNG', 'svg_to_png.py', ['Claude looks at it,', 'finds overlaps'], 'figure.png'),
            ('document', 'Build .docx', 'docx_helpers.py', ['Styles, tables, bullets,', 'captions, SVG'], 'proposal.docx'),
            ('print', 'Export', 'word_to_pdf.py', ['hwp_convert.py for', 'HWP, HWPX, PDF'], '.pdf  .hwp'),
            ('ruler', 'Check', 'pdf_check.py', ['lint_ko.py for tone,', 'punctuation, captions'], 'report'),
        ],
        loops=('Fix overlaps and clipping', 'Over the limit? Trim and rebuild'),
        out='how-it-works-en'),
}

MONO = "Consolas, 'D2Coding', monospace"


def mono(c, x, y, s, size, fill, weight=600, anchor='middle'):
    c.els.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="%d" font-weight="%d" fill="%s" '
                 'text-anchor="%s">%s</text>' % (x, y, MONO, size, weight, fill, anchor, c.esc(s)))


def draw(t):
    W, H = 1800, 590
    c = sd.Canvas(W, H)
    # 규칙 띠
    c.rect(0, 0, W, 104, C['ai'], C['ailine'], 2.5, 18)
    c.circle(66, 52, 36, C['white'], C['ailine'], 2.5)
    c.icon('rules', 66, 52, 46)
    c.text(120, 46, t['band'][0], 28, 800, C['aitext'], 'start')
    c.text(120, 80, t['band'][1], 22, 500, C['aitext'], 'start')

    n = len(t['steps'])
    S = W / n
    xs = [S * (i + 0.5) for i in range(n)]
    PY = 210
    # 규칙이 모든 단계에 들어감
    for x in xs:
        c.arrow([(x, 106), (x, PY - 60)], color=C['ailine'], width=2.2)
    # 길
    c.line([(xs[0], PY), (xs[-1], PY)], C['path'], 12)
    for i in range(n - 1):
        mx = (xs[i] + xs[i + 1]) / 2
        c.poly([(mx + 12, PY), (mx - 8, PY - 12), (mx - 8, PY + 12)], C['ailine'])

    for i, ((ic, title, script, desc, out), cx) in enumerate(zip(t['steps'], xs)):
        c.circle(cx, PY, 56, C['white'], C['personline'], 2.5)
        c.icon(ic, cx, PY, 68)
        c.circle(cx - 42, PY - 42, 15, C['blue'])
        c.text(cx - 42, PY - 35, str(i + 1), 19, 800, C['white'])
        c.text(cx, PY + 100, title, 28, 800, C['ink'])
        mono(c, cx, PY + 132, script, 21, C['blue'])
        c.text(cx, PY + 170, desc[0], 22, 400, C['body'])
        c.text(cx, PY + 198, desc[1], 22, 400, C['body'])
        cw = S - 46
        c.rect(cx - cw / 2, PY + 222, cw, 52, C['white'], C['ink'], 2.5, 12)
        c.icon('file', cx - cw / 2 + 28, PY + 248, 30)
        if out.isascii():
            mono(c, cx + 12, PY + 256, out, 21, C['ink'], 700)
        else:
            c.text(cx + 12, PY + 256, out, 22, 700, C['ink'])

    # 되돌아가는 고리
    yb = PY + 276
    for a, b, lab in [(2, 1, t['loops'][0]), (5, 3, t['loops'][1])]:
        y = yb + 62
        c.arrow([(xs[a], yb + 2), (xs[a], y), (xs[b], y), (xs[b], yb + 4)], color=C['line'], width=2.6)
        lx = (xs[a] + xs[b]) / 2
        wlab = 22 * len(lab) * (0.86 if t is TEXT['ko'] else 0.52) + 60
        c.rect(lx - wlab / 2, y - 22, wlab, 42, C['white'], C['tierline'], 1.8, 21)
        c.icon('redo', lx - wlab / 2 + 24, y - 1, 24)
        c.text(lx + 12, y + 7, lab, 21, 700, C['ink'])
    svg = os.path.join(HERE, t['out'] + '.svg')
    c.save(svg)
    subprocess.run([sys.executable, os.path.join(SCRIPTS, 'svg_to_png.py'), svg, os.path.join(HERE, t['out'] + '.png'),
                    '--width', '2400'], check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


for t in TEXT.values():
    draw(t)
