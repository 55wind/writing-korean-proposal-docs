# -*- coding: utf-8 -*-
"""PDF 점검: 쪽수, 쪽마다 본문 아래 남은 여백(mm), 들어간 글꼴, 쪽별 래스터 이미지 수.

    python pdf_check.py out.pdf [--body-end 284.5]     # body-end = 쪽 높이 - 아래 여백 (mm)

- 남은 여백이 0에 가까운 쪽은 내용을 더하면 다음 쪽으로 넘친다.
- 글꼴 목록에 Calibri, Cambria Math 같은 대체 글꼴이 보이면 지정 글꼴이나 특수 공백 문자를 Word가 못 찾은 것.
- 글자만 있는 쪽에 래스터 이미지가 수백 개면 Word가 글꼴을 PDF에 못 넣어 글자를 그림으로 바꾼 것 (OTF 설치가 원인).
"""
import sys as _sys
_sys.stdout.reconfigure(encoding="utf-8")
import sys

import fitz

pdf = sys.argv[1]
end = float(sys.argv[sys.argv.index('--body-end') + 1]) if '--body-end' in sys.argv else 284.5
d = fitz.open(pdf)


def mm(v):
    return v * 25.4 / 72


fonts, rows = set(), []
for i, p in enumerate(d):
    ys = [mm(b[3]) for b in p.get_text('blocks')] + [mm(r['rect'].y1) for r in p.get_drawings()]
    ys += [mm(x['bbox'][3]) for x in p.get_image_info()]
    ys = [y for y in ys if y < end + 1.5]
    fonts |= {f[3].split('+')[-1] for f in p.get_fonts()}
    rows.append('%2d쪽  남은 여백 %5.1fmm  래스터 이미지 %d' % (i + 1, end - max(ys) if ys else end, len(p.get_images())))
print('%s: %d쪽' % (pdf, d.page_count))
print('\n'.join(rows))
print('글꼴:', ', '.join(sorted(fonts)))
