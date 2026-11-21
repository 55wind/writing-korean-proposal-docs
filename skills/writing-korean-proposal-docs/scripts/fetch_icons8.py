# -*- coding: utf-8 -*-
"""Icons8 Flat Color Icons(MIT, 상업 사용 무료, 출처 표기 불필요)를 내려받고 후보 시트를 만든다.

    python fetch_icons8.py --list                    # 아이콘 이름 329개 출력
    python fetch_icons8.py <폴더> name1 name2 ...    # SVG 저장 + <폴더>/_sheet.png (이름표 붙은 미리보기)
"""
import sys as _sys
_sys.stdout.reconfigure(encoding="utf-8")
import json
import os
import sys
import urllib.request

PKG = 'https://cdn.jsdelivr.net/npm/flat-color-icons@1.1.0'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'icons-fetch'})
    return urllib.request.urlopen(req, timeout=30).read()


if sys.argv[1:2] == ['--list']:
    d = json.loads(get('https://data.jsdelivr.com/v1/package/npm/flat-color-icons@1.1.0/flat'))
    print(' '.join(sorted(f['name'][5:-4] for f in d['files'] if f['name'].startswith('/svg/'))))
    sys.exit()

out, names = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
for n in names:
    with open(os.path.join(out, n + '.svg'), 'wb') as f:
        f.write(get('%s/svg/%s.svg' % (PKG, n)))
with open(os.path.join(out, 'LICENSE.txt'), 'w', encoding='utf-8') as f:
    f.write('Icons8 Flat Color Icons (https://github.com/icons8/flat-color-icons)\n'
            'MIT 또는 Good Boy License. "free icons for personal and commercial use. No credits required."\n')
try:
    import fitz
    from PIL import Image, ImageDraw
    cols, cell = 10, 120
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell, rows * (cell + 20)), 'white')
    dr = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        pix = fitz.open(os.path.join(out, n + '.svg'))[0].get_pixmap(dpi=150)
        mode = 'RGBA' if pix.alpha else 'RGB'
        im = Image.frombytes(mode, (pix.width, pix.height), pix.samples).convert('RGB').resize((84, 84))
        x, y = (i % cols) * cell + 18, (i // cols) * (cell + 20) + 6
        sheet.paste(im, (x, y))
        dr.text((x - 14, y + 88), n[:18], fill='black')
    sheet.save(os.path.join(out, '_sheet.png'))
    print('saved', len(names), 'icons + _sheet.png')
except ImportError:
    print('saved', len(names), 'icons (PyMuPDF나 Pillow가 없어 시트는 생략)')
