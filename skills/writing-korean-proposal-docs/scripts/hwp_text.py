# -*- coding: utf-8 -*-
"""한글(.hwp, .hwpx), Word(.docx), PDF, 텍스트 파일에서 문단 글자를 뽑는다. 한컴오피스가 없어도 된다.

    python hwp_text.py 문서.hwp            # 문단마다 한 줄 (표 안 글자 포함)
    python hwp_text.py 문서.hwpx --eq      # 수식 스크립트도 [EQ] 줄로 함께 출력

다른 스크립트에서는 paragraphs(path)를 쓴다: (위치 이름, 글자) 목록을 돌려준다.
- .hwp  : HWP 5.0 바이너리. BodyText/Section* 스트림의 PARA_TEXT 레코드를 읽음 (olefile 필요)
- .hwpx : Contents/section*.xml의 <hp:p>마다 바로 아래 <hp:run>/<hp:t> 글자를 모음 (표 안 문단은 따로 한 줄)
- .docx : 본문과 표의 <w:p>마다 <w:t> 글자를 모음
- .pdf  : 쪽마다 줄 단위 (PyMuPDF 필요)
배포용(읽기 전용)으로 저장된 .hwp는 본문이 암호화돼 있어 읽지 못한다.
"""
import os
import re
import struct
import sys
import zipfile
import zlib
import xml.etree.ElementTree as ET

HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


# ---------------- .hwp (HWP 5.0) ----------------
def _records(buf):
    i = 0
    while i + 4 <= len(buf):
        h = struct.unpack_from('<I', buf, i)[0]
        i += 4
        tag, lvl, sz = h & 0x3ff, (h >> 10) & 0x3ff, (h >> 20) & 0xfff
        if sz == 0xfff:
            sz = struct.unpack_from('<I', buf, i)[0]
            i += 4
        yield tag, lvl, buf[i:i + sz]
        i += sz


_CHAR1 = {0, 10, 13, 24, 25, 26, 27, 28, 29, 30, 31}  # 1글자짜리 제어 문자. 나머지 제어 문자는 8글자(16바이트)를 차지함


def _para_text(data):
    out, j, n = [], 0, len(data) // 2
    while j < n:
        c = struct.unpack_from('<H', data, j * 2)[0]
        if c < 32:
            if c == 9:
                out.append('\t')
            j += 1 if c in _CHAR1 else 8
        else:
            out.append(chr(c))
            j += 1
    return ''.join(out).rstrip('\r\n')


def _hwp(path, eq):
    import olefile
    ole = olefile.OleFileIO(path)
    props = struct.unpack_from('<I', ole.openstream('FileHeader').read(), 36)[0]
    if props & 4:
        raise SystemExit('배포용 문서라 본문을 읽을 수 없음: %s' % path)
    compressed = props & 1
    secs = sorted([e for e in ole.listdir() if e[0] == 'BodyText'], key=lambda e: int(e[1][7:]))
    out = []
    for e in secs:
        raw = ole.openstream(e).read()
        buf = zlib.decompress(raw, -15) if compressed else raw
        k = 0
        for tag, lvl, data in _records(buf):
            if tag == 67:  # HWPTAG_PARA_TEXT
                k += 1
                out.append(('%s 문단 %d' % (e[1], k), _para_text(data)))
            elif tag == 88 and eq:  # HWPTAG_EQEDIT
                ln = struct.unpack_from('<H', data, 4)[0]
                out.append(('%s 문단 %d 수식' % (e[1], k), '[EQ] ' + data[6:6 + ln * 2].decode('utf-16le', 'replace')))
    return out


# ---------------- .hwpx ----------------
def _hwpx(path, eq):
    out = []
    with zipfile.ZipFile(path) as z:
        names = sorted([n for n in z.namelist() if re.fullmatch(r'Contents/section\d+\.xml', n)],
                       key=lambda n: int(re.search(r'\d+', n.split('/')[-1]).group()))
        for n in names:
            root = ET.fromstring(z.read(n))
            for k, p in enumerate(root.iter(HP + 'p'), 1):
                txt = ''.join(''.join(t.itertext()) for run in p.findall(HP + 'run') for t in run.findall(HP + 't'))
                out.append(('%s 문단 %d' % (n.split('/')[-1][:-4], k), txt))
                if eq:
                    for run in p.findall(HP + 'run'):
                        for e_ in run.findall(HP + 'equation'):
                            s = e_.find(HP + 'script')
                            if s is not None and s.text:
                                out.append(('%s 문단 %d 수식' % (n.split('/')[-1][:-4], k), '[EQ] ' + s.text))
    return out


# ---------------- .docx / .pdf / text ----------------
def _docx(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    return [('문단 %d' % k, ''.join(t.text or '' for t in p.iter(W + 't'))) for k, p in enumerate(root.iter(W + 'p'), 1)]


def _pdf(path):
    import pymupdf
    out = []
    for i, page in enumerate(pymupdf.open(path), 1):
        for k, line in enumerate(page.get_text().splitlines(), 1):
            out.append(('%d쪽 %d줄' % (i, k), line))
    return out


def paragraphs(path, eq=False):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.hwp':
        return _hwp(path, eq)
    if ext == '.hwpx':
        return _hwpx(path, eq)
    if ext == '.docx':
        return _docx(path)
    if ext == '.pdf':
        return _pdf(path)
    with open(path, encoding='utf-8') as f:
        return [('%d줄' % k, s.rstrip('\n')) for k, s in enumerate(f, 1)]


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for _, s in paragraphs(sys.argv[1], eq='--eq' in sys.argv):
        print(s)
