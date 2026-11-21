# -*- coding: utf-8 -*-
"""Word로 docx -> PDF 내보내기 (Windows + Microsoft Word 필요).

    python word_to_pdf.py <in.docx> [out.pdf] [--embed-fonts] [--pages N]
    out.pdf를 빼면 같은 이름의 .pdf. --pages N이면 쪽수가 N을 넘을 때 경고.

--embed-fonts: PDF로 내보내기 전에 docx에 글꼴(Pretendard TTF)을 넣어 저장한다.
               Pretendard가 없는 PC에서도 같은 모양으로 열고 고칠 수 있다.
PDF에 글꼴이 그림으로 들어가지 않으려면 Pretendard가 TrueType(.ttf)으로 설치돼 있어야 한다
(OTF로 설치돼 있으면 Word가 글자를 그림으로 바꿔 넣는다).
"""
import sys as _sys
_sys.stdout.reconfigure(encoding="utf-8")
import os, sys
import pythoncom
import win32com.client

embed = '--embed-fonts' in sys.argv
limit = int(sys.argv[sys.argv.index('--pages') + 1]) if '--pages' in sys.argv else None
args = [a for a in sys.argv[1:] if not a.startswith('--') and not a.isdigit()] + [None, None]
src = os.path.abspath(args[0])
dst = os.path.abspath(args[1] or os.path.splitext(src)[0] + '.pdf')
pythoncom.CoInitialize()
word = win32com.client.DispatchEx('Word.Application')
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Open(src, ConfirmConversions=False, ReadOnly=not embed, AddToRecentFiles=False, Visible=False)
    if embed:
        doc.EmbedTrueTypeFonts = True
        doc.SaveSubsetFonts = False  # 글꼴 전체를 넣어야 다른 PC에서 새 글자도 고칠 수 있음
        doc.DoNotEmbedSystemFonts = True
        doc.Save()
    doc.Fields.Update()  # 본문 필드(캡션 번호 SEQ 등)
    doc.Repaginate()
    for s in doc.Sections:
        for h in list(s.Headers) + list(s.Footers):
            h.Range.Fields.Update()
    pages = doc.ComputeStatistics(2)  # wdStatisticPages
    # 17 = PDF, OptimizeFor 0 = 인쇄 품질, Range 0 = 문서 전체, Item 0 = 본문, CreateBookmarks 1 = 제목으로 책갈피
    doc.ExportAsFixedFormat(OutputFileName=dst, ExportFormat=17, OpenAfterExport=False, OptimizeFor=0, Range=0,
                            Item=0, IncludeDocProps=True, KeepIRM=True, CreateBookmarks=1, DocStructureTags=True,
                            BitmapMissingFonts=True, UseISO19005_1=False)
    doc.Close(SaveChanges=0)
    print('pages', pages, '->', dst)
    if limit and pages > limit:
        print('경고: %d쪽으로 제한 %d쪽을 넘음' % (pages, limit))
finally:
    word.Quit()
