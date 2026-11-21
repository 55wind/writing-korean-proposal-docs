# -*- coding: utf-8 -*-
"""SVG를 PNG로 바꾼다. 헤드리스 Chromium(Playwright)으로 그리므로 설치된 글꼴(Pretendard 등)이 그대로 쓰인다.

    python svg_to_png.py in.svg [out.png] [--width 3600]

준비: pip install playwright && python -m playwright install chromium
"""
import sys as _sys
_sys.stdout.reconfigure(encoding="utf-8")
import base64
import os
import sys

from playwright.sync_api import sync_playwright

argv = sys.argv[1:]
width = 3600
if '--width' in argv:
    k = argv.index('--width')
    width = int(argv[k + 1])
    del argv[k:k + 2]
src = os.path.abspath(argv[0])
dst = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.splitext(src)[0] + '.png'
uri = 'data:image/svg+xml;base64,' + base64.b64encode(open(src, 'rb').read()).decode()

JS = """([uri, W]) => new Promise((ok, fail) => {
  const im = new Image();
  im.onload = () => {
    const H = Math.round(im.naturalHeight * W / im.naturalWidth);
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, W, H); g.drawImage(im, 0, 0, W, H);
    ok(c.toDataURL('image/png'));
  };
  im.onerror = () => fail('SVG를 그리지 못함 (SVG 문법이나 foreignObject를 확인)');
  im.src = uri;
})"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_content('<!doctype html><meta charset="utf-8"><body></body>')
    data = page.evaluate(JS, [uri, width])
    browser.close()
with open(dst, 'wb') as f:
    f.write(base64.b64decode(data.split(',', 1)[1]))
print('saved', dst)
