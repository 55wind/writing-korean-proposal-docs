# -*- coding: utf-8 -*-
"""한컴오피스 한글로 문서 형식을 바꾼다 (Windows + 한컴오피스 한글 2018 이상, pywin32 필요).

    python hwp_convert.py 기획안.docx 기획안.hwp --try-docx   # Word 문서를 한글 문서로 (아래 주의)
    python hwp_convert.py 기획안.hwp  기획안.hwpx      # 글자를 고치려고 HWPX로 (hwpx_replace.py)
    python hwp_convert.py 기획안.hwpx 기획안.hwp
    python hwp_convert.py 기획안.hwp  기획안.pdf       # 제출용 PDF와 쪽수 확인

입력: .hwp .hwpx .docx .doc / 출력: .hwp .hwpx .pdf .docx (확장자로 정함)
한 번 실행에 한 번만 바꾼다. 같은 한글 세션에서 HWP 저장 뒤 바로 PDF 저장을 하면 한글이 멈추는 일이 있어서다.

꼭 알아 둘 것
- 한글 창에 다른 문서가 열려 있으면 자동화 연결이 멈출 수 있다. 바꾸기 전에 한글 문서를 모두 닫는다.
- 자동화로 파일을 열면 한글이 "접근 허용" 보안 창을 띄워 멈춘다. 보안 모듈(FilePathCheckerModule.dll)을 등록하면 뜨지 않는다.
  --security-dll 경로, 환경 변수 HWP_SECURITY_DLL, 또는 pip로 설치한 pyhwpx 패키지에 든 DLL 순서로 찾는다.
  보안 모듈은 한컴 개발자 사이트(developer.hancom.com)의 한글 자동화 자료에서 받을 수 있다.
- 경로에 한글이 들어 있을 때 한글이 말없이 멈추는 경우가 있다. 그러면 영문 경로로 복사해서 바꾼다.
- .docx, .doc 입력은 --try-docx를 줘야 시도한다. 한컴오피스 2018은 자동화로 docx를 열면 한글 대신 한워드(Hword.exe)를
  띄우고 열기에 실패하며, 한워드 시작 화면이 화면에 남아 다음 자동화까지 막는다. 그러면 Hword.exe를 끄고,
  docx는 한글에서 직접 열어 '다른 이름으로 저장'으로 .hwp를 만든다.
- --timeout 초 안에 끝나지 않으면 멈춘 것으로 보고 종료한다. 이때 남은 숨은 Hwp.exe는 작업 관리자에서 끈다.
"""
import argparse
import glob
import importlib.util
import os
import sys
import threading

FMT_OUT = {'.hwp': 'HWP', '.hwpx': 'HWPX', '.pdf': 'PDF', '.docx': 'OOXML'}
FMT_IN = {'.hwp': ['HWP'], '.hwpx': ['HWPX'], '.docx': ['', 'OOXML', 'MSWORD'], '.doc': ['MSWORD', '']}  # 앞에서부터 시도


def find_security_dll(arg):
    for c in [arg, os.environ.get('HWP_SECURITY_DLL')]:
        if c and os.path.isfile(c):
            return c
    spec = importlib.util.find_spec('pyhwpx')
    if spec and spec.origin:
        hits = glob.glob(os.path.join(os.path.dirname(spec.origin), 'FilePathCheckerModule*.dll'))
        if hits:
            return hits[0]
    return None


def register_security(dll):
    import winreg
    k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\HNC\HwpAutomation\Modules')
    winreg.SetValueEx(k, 'FilePathCheckerModule', 0, winreg.REG_SZ, dll)


def main():
    ap = argparse.ArgumentParser(description='한글로 문서 형식 바꾸기')
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--security-dll')
    ap.add_argument('--timeout', type=int, default=180)
    ap.add_argument('--try-docx', action='store_true', help='docx, doc 입력을 시도함 (한컴오피스 2018은 한워드가 떠서 실패함)')
    a = ap.parse_args()
    src, dst = os.path.abspath(a.src), os.path.abspath(a.dst)
    ein, eout = os.path.splitext(src)[1].lower(), os.path.splitext(dst)[1].lower()
    if ein in ('.docx', '.doc') and not a.try_docx:
        raise SystemExit('docx, doc 입력은 한글 버전에 따라 한워드가 떠서 멈출 수 있음. 한글에서 직접 열어 다른 이름으로 '
                         '저장하거나, 시도하려면 --try-docx를 붙이세요.')
    if eout not in FMT_OUT:
        raise SystemExit('출력 확장자는 %s 중 하나: %s' % (', '.join(FMT_OUT), dst))

    def watchdog():
        print('%d초 안에 끝나지 않아 멈춘 것으로 봄. 한글 문서를 모두 닫거나 영문 경로로 옮겨 다시 실행하세요.' % a.timeout,
              flush=True)
        os._exit(2)
    timer = threading.Timer(a.timeout, watchdog)
    timer.daemon = True
    timer.start()

    dll = find_security_dll(a.security_dll)
    if dll:
        register_security(dll)
    else:
        print('보안 모듈을 찾지 못함. 한글이 파일 접근 허용 창을 띄우면 멈출 수 있음 (--security-dll 참고)', flush=True)

    import pythoncom
    import win32com.client as wc
    pythoncom.CoInitialize()
    hwp = wc.dynamic.Dispatch('HWPFrame.HwpObject')
    try:
        hwp.XHwpWindows.Item(0).Visible = False
    except Exception:
        pass
    if dll:
        hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')
    hwp.SetMessageBoxMode(0x00020020)  # 확인 창은 '확인', 예/아니요 창은 '예'로 자동 응답
    try:
        for f in FMT_IN.get(ein, ['']):
            if hwp.Open(src, f, 'forceopen:true'):
                print('열기 형식 %r' % f, flush=True)
                break
        else:
            raise SystemExit('열지 못함: %s' % src)
        pages = hwp.PageCount
        ok = hwp.SaveAs(dst, FMT_OUT[eout], '')
        print('%s -> %s (%d쪽) %s' % (os.path.basename(src), dst, pages, '완료' if ok and os.path.exists(dst) else '실패'))
    finally:
        try:
            hwp.Clear(1)
            hwp.Quit()
        except Exception:
            pass
        timer.cancel()


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
