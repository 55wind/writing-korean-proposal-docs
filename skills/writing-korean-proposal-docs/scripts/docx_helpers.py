# -*- coding: utf-8 -*-
"""python-docx 도우미: 스키마 순서를 지키는 XML 편집, 표, 칸 서식, 글꼴, 필드, SVG 그림(PNG 대체 포함).

    from docx_helpers import *
    SCALE["size"] = 1.12   # 글자 배율
    para(doc, "본문 <b>굵게</b> <g>+11개</g>", first=3.5)
    t = table(doc, rows, [24, 156], borders={...}); cell(c, shade=C["ground"], valign="center"); fill(c, "글<br/>줄바꿈")
    picture_svg(p, "fig.png", "fig.svg", 180, doc.part)
"""
import re
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml, OxmlElement

FONT_LATIN = 'Pretendard'
FONT_EA = 'Pretendard'
C = dict(blue='3F58D4', deep='3043A1', wash='F2F4FC', tint='D5DBF6', ink='111111', body='333333',
         soft='555555', faint='757575', line='DDDDDD', lsoft='EEEEEE', ground='F5F6F8', box='F5F5F5',
         green='1C824A', orange='C05119', white='FFFFFF', phone='CDD1DA', arrow='A9AEBA')

PPR = ['w:pStyle', 'w:keepNext', 'w:keepLines', 'w:pageBreakBefore', 'w:framePr', 'w:widowControl', 'w:numPr',
       'w:suppressLineNumbers', 'w:pBdr', 'w:shd', 'w:tabs', 'w:suppressAutoHyphens', 'w:kinsoku', 'w:wordWrap',
       'w:overflowPunct', 'w:topLinePunct', 'w:autoSpaceDE', 'w:autoSpaceDN', 'w:bidi', 'w:adjustRightInd',
       'w:snapToGrid', 'w:spacing', 'w:ind', 'w:contextualSpacing', 'w:mirrorIndents', 'w:suppressOverlap', 'w:jc',
       'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap', 'w:outlineLvl', 'w:divId', 'w:cnfStyle', 'w:rPr',
       'w:sectPr', 'w:pPrChange']
RPR = ['w:rStyle', 'w:rFonts', 'w:b', 'w:bCs', 'w:i', 'w:iCs', 'w:caps', 'w:smallCaps', 'w:strike', 'w:dstrike',
       'w:outline', 'w:shadow', 'w:emboss', 'w:imprint', 'w:noProof', 'w:snapToGrid', 'w:vanish', 'w:webHidden',
       'w:color', 'w:spacing', 'w:w', 'w:kern', 'w:position', 'w:sz', 'w:szCs', 'w:highlight', 'w:u', 'w:effect',
       'w:bdr', 'w:shd', 'w:fitText', 'w:vertAlign', 'w:rtl', 'w:cs', 'w:em', 'w:lang', 'w:eastAsianLayout',
       'w:specVanish', 'w:oMath']
TCPR = ['w:cnfStyle', 'w:tcW', 'w:gridSpan', 'w:hMerge', 'w:vMerge', 'w:tcBorders', 'w:shd', 'w:noWrap', 'w:tcMar',
        'w:textDirection', 'w:tcFitText', 'w:vAlign', 'w:hideMark']
TBLPR = ['w:tblStyle', 'w:tblpPr', 'w:tblOverlap', 'w:bidiVisual', 'w:tblStyleRowBandSize', 'w:tblStyleColBandSize',
         'w:tblW', 'w:jc', 'w:tblCellSpacing', 'w:tblInd', 'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar',
         'w:tblLook', 'w:tblCaption', 'w:tblDescription']
BDR = ['w:top', 'w:left', 'w:bottom', 'w:right', 'w:insideH', 'w:insideV', 'w:tl2br', 'w:tr2bl']
PBDR = ['w:top', 'w:left', 'w:bottom', 'w:right', 'w:between', 'w:bar']
MAR = ['w:top', 'w:left', 'w:bottom', 'w:right']


SCALE = {'size': 1.0, 'line': 1.0}


def tw(mm):  # mm -> twips
    return int(round(mm * 1440 / 25.4))


def mm2pt(mm):
    return mm * 72 / 25.4


def child(parent, tag, seq, attrs=None):
    el = parent.find(qn(tag))
    if el is None:
        el = OxmlElement(tag)
        later = {qn(t) for t in seq[seq.index(tag) + 1:]}
        for ch in parent:
            if ch.tag in later:
                ch.addprevious(el)
                break
        else:
            parent.append(el)
    if attrs:
        for k, v in attrs.items():
            el.set(qn(k), str(v))
    return el


def set_rfonts(rPr):
    rf = child(rPr, 'w:rFonts', RPR)
    for a in list(rf.attrib):
        del rf.attrib[a]
    rf.set(qn('w:ascii'), FONT_LATIN)
    rf.set(qn('w:hAnsi'), FONT_LATIN)
    rf.set(qn('w:eastAsia'), FONT_EA)
    rf.set(qn('w:cs'), FONT_LATIN)


def rfmt(rPr, size=None, bold=None, color=None, italic=None, sup=False, shade=None, spacing=None, position=None):
    if bold is not None:
        child(rPr, 'w:b', RPR, {'w:val': '1' if bold else '0'})
        child(rPr, 'w:bCs', RPR, {'w:val': '1' if bold else '0'})
    if italic is not None:
        child(rPr, 'w:i', RPR, {'w:val': '1' if italic else '0'})
    if color:
        c = child(rPr, 'w:color', RPR)
        for a in list(c.attrib):
            del c.attrib[a]
        c.set(qn('w:val'), color)
    if spacing is not None:
        child(rPr, 'w:spacing', RPR, {'w:val': int(round(spacing * 20))})
    if position is not None:
        child(rPr, 'w:position', RPR, {'w:val': int(round(position * 2))})
    if size:
        size = size * SCALE['size'] if size > 1.5 else size
        child(rPr, 'w:sz', RPR, {'w:val': int(round(size * 2))})
        child(rPr, 'w:szCs', RPR, {'w:val': int(round(size * 2))})
    if shade:
        child(rPr, 'w:shd', RPR, {'w:val': 'clear', 'w:color': 'auto', 'w:fill': shade})
    if sup:
        child(rPr, 'w:vertAlign', RPR, {'w:val': 'superscript'})


def pfmt(p, line=None, before=None, after=None, align=None, keep_next=None, keep_lines=None, pbb=None,
         ind_left=None, hanging=None, first=None, shade=None, bdr=None, tabs=None, auto_line=None, outline=None,
         widow=None):
    """line/before/after in pt; ind in mm; bdr = {side: (pt, color, space_pt)}"""
    pPr = p._p.get_or_add_pPr() if hasattr(p, '_p') else p
    if keep_next is not None:
        child(pPr, 'w:keepNext', PPR, {'w:val': '1' if keep_next else '0'})
    if keep_lines is not None:
        child(pPr, 'w:keepLines', PPR, {'w:val': '1' if keep_lines else '0'})
    if pbb is not None:
        child(pPr, 'w:pageBreakBefore', PPR, {'w:val': '1' if pbb else '0'})
    if widow is not None:
        child(pPr, 'w:widowControl', PPR, {'w:val': '1' if widow else '0'})
    if bdr:
        pb = child(pPr, 'w:pBdr', PPR)
        for side, spec in bdr.items():
            if spec is None:
                child(pb, 'w:' + side, PBDR, {'w:val': 'nil'})
            else:
                ptw, col, sp = spec
                child(pb, 'w:' + side, PBDR, {'w:val': 'single', 'w:sz': int(round(ptw * 8)), 'w:space': sp,
                                               'w:color': col})
    if shade:
        child(pPr, 'w:shd', PPR, {'w:val': 'clear', 'w:color': 'auto', 'w:fill': shade})
    if tabs:
        t = child(pPr, 'w:tabs', PPR)
        for pos_mm, kind in tabs:
            el = OxmlElement('w:tab')
            el.set(qn('w:val'), kind)
            el.set(qn('w:pos'), str(tw(pos_mm)))
            t.append(el)
    if line is not None or before is not None or after is not None or auto_line:
        sp = child(pPr, 'w:spacing', PPR)
        if before is not None:
            sp.set(qn('w:before'), str(int(round(before * 20))))
            sp.set(qn('w:beforeAutospacing'), '0')
        if after is not None:
            sp.set(qn('w:after'), str(int(round(after * 20))))
            sp.set(qn('w:afterAutospacing'), '0')
        if line is not None:
            if line > 3:
                line = line * SCALE['line']
            sp.set(qn('w:line'), str(int(round(line * 20))))
            sp.set(qn('w:lineRule'), 'exact')
        if auto_line:
            sp.set(qn('w:line'), str(int(round(auto_line * 240))))
            sp.set(qn('w:lineRule'), 'auto')
    if ind_left is not None or hanging is not None or first is not None:
        ind = child(pPr, 'w:ind', PPR)
        if ind_left is not None:
            ind.set(qn('w:left'), str(tw(ind_left)))
        if hanging is not None:
            ind.set(qn('w:hanging'), str(tw(hanging)))
        if first is not None:
            ind.set(qn('w:firstLine'), str(tw(first)))
    if align:
        child(pPr, 'w:jc', PPR, {'w:val': {'left': 'left', 'center': 'center', 'right': 'right',
                                           'both': 'both'}[align]})
    if outline is not None:
        child(pPr, 'w:outlineLvl', PPR, {'w:val': outline})


TAGS = {  # 본문 글씨는 검정 한 가지. 강조는 굵게만 한다
    'b': dict(bold=True, color=C['ink']),
    'bl': dict(bold=True, color=C['ink']),
    'bd': dict(bold=True, color=C['ink']),
    'g': dict(bold=True, color=C['ink']),
    'o': dict(bold=True, color=C['ink']),
    'soft': dict(bold=False, color=C['ink']),
    'sm': dict(bold=False, color=C['ink']),
    'sup': dict(sup=True, bold=True, color=C['ink']),
    'big': dict(),
    'nb': dict(bold=False),
    'w': dict(color=C['white']),
}
TAG_RE = re.compile(r'(<br/>|</?(?:%s)>)' % '|'.join(TAGS))


def curly(s):
    s = re.sub(r'"([^"]*)"', '“\\1”', s)
    s = re.sub(r"'([^']*)'", '‘\\1’', s)
    return s


def runs(p, markup, **base):
    """Add runs parsed from tiny markup. base: rfmt kwargs applied to every run."""
    stack = []
    for tok in TAG_RE.split(curly(markup)):
        if not tok:
            continue
        if tok == '<br/>':
            r = p.add_run()
            r.add_break()
            continue
        m = re.fullmatch(r'<(/?)(\w+)>', tok)
        if m and m.group(2) in TAGS:
            if m.group(1):
                stack.pop()
            else:
                stack.append(m.group(2))
            continue
        f = dict(base)
        for s in stack:
            f.update(TAGS[s])
        r = p.add_run(tok)
        rfmt(r._r.get_or_add_rPr(), **f)
    return p


def para(container, markup='', style=None, run=None, **pf):
    p = container.add_paragraph(style=style)
    pfmt(p, **pf)
    if markup:
        runs(p, markup, **(run or {}))
    return p


def gap(container, mm):
    p = container.add_paragraph()
    pfmt(p, line=max(mm2pt(mm), 1), before=0, after=0)
    r = p.add_run()
    rfmt(r._r.get_or_add_rPr(), size=1)
    return p


# ---------- tables ----------

def border_spec(el, seq, spec):
    for side, s in spec.items():
        if s is None:
            child(el, 'w:' + side, seq, {'w:val': 'nil'})
        else:
            ptw, col = s
            child(el, 'w:' + side, seq, {'w:val': 'single', 'w:sz': int(round(ptw * 8)), 'w:space': 0,
                                         'w:color': col})


NONE = {k: None for k in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']}


def table(container, rows, widths, borders=None, mar=(1.3, 2, 1.3, 2), align=None):
    t = container.add_table(rows=rows, cols=len(widths))
    tblPr = t._tbl.tblPr
    st = tblPr.find(qn('w:tblStyle'))
    if st is not None:
        tblPr.remove(st)
    child(tblPr, 'w:tblW', TBLPR, {'w:w': tw(sum(widths)), 'w:type': 'dxa'})
    if align:
        child(tblPr, 'w:jc', TBLPR, {'w:val': align})
    child(tblPr, 'w:tblInd', TBLPR, {'w:w': 0, 'w:type': 'dxa'})
    b = child(tblPr, 'w:tblBorders', TBLPR)
    spec = dict(NONE)
    spec.update(borders or {})
    border_spec(b, BDR, spec)
    child(tblPr, 'w:tblLayout', TBLPR, {'w:type': 'fixed'})
    cm = child(tblPr, 'w:tblCellMar', TBLPR)
    for side, v in zip(['top', 'left', 'bottom', 'right'], mar):
        child(cm, 'w:' + side, MAR, {'w:w': tw(v), 'w:type': 'dxa'})
    look = tblPr.find(qn('w:tblLook'))
    if look is not None:
        tblPr.remove(look)
    grid = t._tbl.tblGrid
    for gc, w in zip(grid.findall(qn('w:gridCol')), widths):
        gc.set(qn('w:w'), str(tw(w)))
    for row in t.rows:
        for c, w in zip(row.cells, widths):
            child(c._tc.get_or_add_tcPr(), 'w:tcW', TCPR, {'w:w': tw(w), 'w:type': 'dxa'})
    return t


def cell(c, shade=None, borders=None, mar=None, valign=None):
    tcPr = c._tc.get_or_add_tcPr()
    if borders:
        b = child(tcPr, 'w:tcBorders', TCPR)
        border_spec(b, BDR, borders)
    if shade:
        child(tcPr, 'w:shd', TCPR, {'w:val': 'clear', 'w:color': 'auto', 'w:fill': shade})
    if mar:
        m = child(tcPr, 'w:tcMar', TCPR)
        for side, v in zip(['top', 'left', 'bottom', 'right'], mar):
            if v is not None:
                child(m, 'w:' + side, MAR, {'w:w': tw(v), 'w:type': 'dxa'})
    if valign:
        child(tcPr, 'w:vAlign', TCPR, {'w:val': valign})
    return c


def row(r, header=False, cant_split=True, height=None, exact=False):
    trPr = r._tr.get_or_add_trPr()
    if cant_split:
        trPr.append(OxmlElement('w:cantSplit'))
    if height is not None:
        r.height = Mm(height)
        r.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY if exact else WD_ROW_HEIGHT_RULE.AT_LEAST
    if header:
        trPr.append(OxmlElement('w:tblHeader'))


def fill(c, items, style='Table Text', run=None, **pf):
    """items: markup string (paragraphs split by <p/>) or list of (markup, pf, run) tuples."""
    if isinstance(items, str):
        items = [(s, {}, {}) for s in items.split('<p/>')]
    first = True
    for it in items:
        if isinstance(it, str):
            it = (it, {}, {})
        mk, ipf, irun = (list(it) + [{}, {}])[:3]
        p = c.paragraphs[0] if first else c.add_paragraph()
        first = False
        p.style = style
        allpf = dict(pf)
        allpf.update(ipf)
        pfmt(p, **allpf)
        allrun = dict(run or {})
        allrun.update(irun)
        if mk:
            runs(p, mk, **allrun)
    return c


def shrink_trailing(c):
    """python-docx leaves an empty paragraph after a nested table; make it 1pt tall."""
    p = c.paragraphs[-1]
    pfmt(p, line=1, before=0, after=0)
    r = p.add_run()
    rfmt(r._r.get_or_add_rPr(), size=1)


def style_pic(r, border='DDDDDD', border_pt=0.5, radius=None, alt=''):
    inline = r._r.find('.//' + qn('wp:inline'))
    if alt:
        inline.find(qn('wp:docPr')).set('descr', alt)
    spPr = inline.find('.//' + qn('pic:spPr'))
    geom = spPr.find(qn('a:prstGeom'))
    if radius is not None:
        geom.set('prst', 'roundRect')
        av = geom.find(qn('a:avLst'))
        if av is None:
            av = OxmlElement('a:avLst')
            geom.append(av)
        for g in list(av):
            av.remove(g)
        av.append(parse_xml('<a:gd %s name="adj" fmla="val %d"/>' % (nsdecls('a'), radius)))
    if border:
        spPr.append(parse_xml('<a:ln %s w="%d"><a:solidFill><a:srgbClr val="%s"/></a:solidFill></a:ln>'
                              % (nsdecls('a'), int(border_pt * 12700), border)))


def picture(p, path, width_mm, **kw):
    r = p.add_run()
    r.add_picture(path, width=Mm(width_mm))
    style_pic(r, **kw)
    return r


def field(p, instr, placeholder, **f):
    def fc(kind):
        r = p.add_run()
        el = OxmlElement('w:fldChar')
        el.set(qn('w:fldCharType'), kind)
        r._r.append(el)
        rfmt(r._r.get_or_add_rPr(), **f)
    fc('begin')
    r = p.add_run()
    it = OxmlElement('w:instrText')
    it.set(qn('xml:space'), 'preserve')
    it.text = ' %s ' % instr
    r._r.append(it)
    rfmt(r._r.get_or_add_rPr(), **f)
    fc('separate')
    r = p.add_run(placeholder)
    rfmt(r._r.get_or_add_rPr(), **f)
    fc('end')


_svg_n = [0]


def picture_svg(p, png_path, svg_path, width_mm, doc_part, alt=''):
    """SVG 그림을 넣는다. Word는 SVG를 그리고, SVG를 못 읽는 프로그램은 같이 넣은 PNG를 보여준다."""
    from docx.opc.part import Part
    from docx.opc.packuri import PackURI
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    r = picture(p, png_path, width_mm, border=None, alt=alt)
    _svg_n[0] += 1
    part = Part(PackURI('/word/media/diagram%d.svg' % _svg_n[0]), 'image/svg+xml', open(svg_path, 'rb').read(),
                doc_part.package)
    rid = doc_part.relate_to(part, RT.IMAGE)
    blip = r._r.find('.//' + qn('a:blip'))
    blip.append(parse_xml(
        '<a:extLst %s><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">'
        '<asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="%s"/>'
        '</a:ext></a:extLst>' % (nsdecls('a'), rid)))
    return r


_CAPN = {'그림': 0, '표': 0}


def caption(container, kind, title):
    """Word 캡션 기능으로 단 제목 (Caption 스타일 + SEQ 필드).

    kind='그림': 그림 바로 아래에 넣는다. 가운데 정렬, '(그림 n) 제목'
    kind='표':   표 바로 앞에 넣는다. 왼쪽 정렬, 다음 문단(표)과 붙임, '<표 n> 제목'
    번호는 넣는 순서대로 매기고, Word에서 필드 업데이트(F9)해도 같은 번호가 나온다.
    """
    _CAPN[kind] += 1
    p = container.add_paragraph(style='Caption')
    if kind == '그림':
        pfmt(p, align='center', before=mm2pt(1.4), after=mm2pt(0.8), keep_next=False)
        o, c_ = '(', ')'
    else:
        pfmt(p, align='left', before=mm2pt(0.6), after=mm2pt(1.0), keep_next=True)
        o, c_ = '<', '>'
    runs(p, o + kind + ' ', bold=True, color=C['ink'])
    field(p, 'SEQ %s \* ARABIC' % kind, str(_CAPN[kind]), bold=True, color=C['ink'])
    runs(p, c_ + ' ', bold=True, color=C['ink'])
    runs(p, title)
    return p
