# -*- coding: utf-8 -*-
"""아이콘 객체로 아키텍처, 서비스 흐름 그림을 그리는 작은 SVG 라이브러리.

    import sys; sys.path.insert(0, r"<이 scripts 폴더>")
    import svgdiagram as sd
    sd.ICON_DIR = r"<아이콘 SVG 폴더>"   # fetch_icons8.py로 받은 폴더
    a = sd.Canvas(1800, 740)            # 1800px = 문서 폭 180mm (1mm = 10px)
    a.tier(0, 0, 250, 440, '이용자')
    a.node(125, 112, 'businessman', '국민', ['휴대폰, PC'], 'person', side='below')
    a.arrow([(171, 112), (258, 186)], '경력 문장', (215, 140))
    a.save(r'out/architecture.svg')

node의 kind(동그라미 테두리로 구분): 'ai' 생성형 AI, 'rule' 규칙 엔진, 'data' 데이터, 'person' 사람과 화면.
Word에 넣을 수 있게 CSS, marker, clipPath, foreignObject, filter는 쓰지 않는다. 글자는 25px(약 7pt) 이상.
"""
import os
import re

ICON_DIR = os.path.join(os.getcwd(), 'icons')  # 쓰는 쪽에서 바꿈
FONT = 'Pretendard'
C = dict(ink='#111111', body='#333333', soft='#5b6170', line='#8a90a0', tier='#f6f7f9', tierline='#dde1e8',
         ai='#eef1fc', ailine='#7e89fd', aitext='#3043a1', data='#eef0f3', dataline='#9aa1ae', blue='#3f58d4',
         person='#ffffff', personline='#d0d4dc', green='#1c824a', white='#ffffff', path='#d5dbf6')
RING = {'person': (C['person'], C['personline'], 2.5), 'ai': (C['ai'], C['ailine'], 3),
        'rule': (C['white'], C['ink'], 4.5), 'data': (C['data'], C['dataline'], 2.5)}
_icons = {}


def icon_body(name):
    """아이콘 SVG(viewBox 0 0 48 48)의 안쪽 도형만 꺼냄"""
    if name not in _icons:
        with open(os.path.join(ICON_DIR, name + '.svg'), encoding='utf-8') as f:
            s = f.read()
        s = re.sub(r'^.*?<svg[^>]*>', '', s, flags=re.S)
        _icons[name] = s.rsplit('</svg>', 1)[0].strip()
    return _icons[name]


class Canvas:
    def __init__(self, w, h):
        self.w, self.h, self.els = w, h, []

    @staticmethod
    def esc(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def text(self, x, y, s, size=23, weight=400, fill=C['body'], anchor='middle'):
        self.els.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="%d" font-weight="%d" fill="%s" '
                        'text-anchor="%s">%s</text>' % (x, y, FONT, size, weight, fill, anchor, self.esc(s)))

    def rect(self, x, y, w, h, fill, stroke=None, sw=2, rx=10):
        st = ' stroke="%s" stroke-width="%g"' % (stroke, sw) if stroke else ''
        self.els.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d" ry="%d" fill="%s"%s/>'
                        % (x, y, w, h, rx, rx, fill, st))

    def circle(self, cx, cy, r, fill, stroke=None, sw=2):
        st = ' stroke="%s" stroke-width="%g"' % (stroke, sw) if stroke else ''
        self.els.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"%s/>' % (cx, cy, r, fill, st))

    def poly(self, pts, fill):
        self.els.append('<polygon points="%s" fill="%s"/>' % (' '.join('%.1f,%.1f' % p for p in pts), fill))

    def line(self, pts, color, width):
        self.els.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%g" stroke-linejoin="round"/>'
                        % (' '.join('%.1f,%.1f' % p for p in pts), color, width))

    def icon(self, name, cx, cy, size):
        s = size / 48.0
        self.els.append('<g transform="translate(%.1f,%.1f) scale(%.4f)">%s</g>'
                        % (cx - size / 2, cy - size / 2, s, icon_body(name)))

    def tier(self, x, y, w, h, title, title_dx=20):
        self.rect(x, y, w, h, C['tier'], C['tierline'], 2, 16)
        self.text(x + title_dx, y + 40, title, 26, 700, C['ink'], 'start')

    def node(self, cx, cy, name, title, subs=(), kind='person', r=46, side='right', tsize=27, ssize=23, lh=28,
             scale=1.25):
        fill, stroke, sw = RING[kind]
        self.circle(cx, cy, r, fill, stroke, sw)
        self.icon(name, cx, cy, r * scale)
        if not title:
            return
        tcol = C['aitext'] if kind == 'ai' else C['ink']
        scol = C['aitext'] if kind == 'ai' else C['soft']
        n = 1 + len(subs)
        if side == 'right':
            x0 = cx + r + 16
            top = cy - (n - 1) * lh / 2 + 9
            self.text(x0, top, title, tsize, 700, tcol, 'start')
            for i, s in enumerate(subs):
                self.text(x0, top + lh * (i + 1), s, ssize, 400, scol, 'start')
        else:
            top = cy + r + 32
            self.text(cx, top, title, tsize, 700, tcol)
            for i, s in enumerate(subs):
                self.text(cx, top + 26 * (i + 1), s, ssize, 400, scol)

    def badge(self, name, cx, cy, size=34):
        """작은 보조 아이콘 (예: 개인정보 자물쇠)"""
        self.circle(cx, cy, size * 0.62, C['white'], C['tierline'], 1.5)
        self.icon(name, cx, cy, size)

    def arrow(self, points, label=None, lpos=None, both=False, color=C['line'], width=2.8):
        self.line(points, color, width)

        def head(p_from, p_to):
            (x1, y1), (x2, y2) = p_from, p_to
            dx, dy = x2 - x1, y2 - y1
            L = (dx * dx + dy * dy) ** 0.5
            ux, uy = dx / L, dy / L
            s = 16
            bx, by = x2 - ux * s, y2 - uy * s
            px, py = -uy * s * 0.55, ux * s * 0.55
            self.poly([(x2, y2), (bx + px, by + py), (bx - px, by - py)], color)
        head(points[-2], points[-1])
        if both:
            head(points[1], points[0])
        if label:
            lx, ly = lpos
            wlab = 23 * len(label) * 0.9 + 16
            self.rect(lx - wlab / 2, ly - 25, wlab, 34, C['white'], C['tierline'], 1.5, 17)
            self.text(lx, ly, label, 22, 600, C['blue'])

    def save(self, path):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n'
               '<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>\n%s\n</svg>\n'
               % (self.w, self.h, self.w, self.h, self.w, self.h, '\n'.join(self.els)))
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(svg)
        print('saved', os.path.abspath(path), '%d KB' % (len(svg) // 1024))
