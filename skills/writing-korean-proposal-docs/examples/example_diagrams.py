# -*- coding: utf-8 -*-
"""예시 기획안(가상의 '동네 공공시설 예약 도우미')의 그림 두 장을 SVG로 그린다.

    python examples/example_diagrams.py
      -> examples/out/architecture.svg  (시스템 아키텍처)
      -> examples/out/service-flow.svg  (서비스 흐름: 예시 인물의 3분 여정)

구성 요소는 무료 아이콘 Icons8 Flat Color Icons(MIT, 출처 표기 불필요)로 그린다. 없는 아이콘은 처음 실행할 때
examples/out/icons/에 내려받는다. 좌표 단위는 px이고 1800px이 문서 폭 180mm에 해당한다 (1mm = 10px, 글자 25px = 약 7pt).
"""
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import svgdiagram as sd  # noqa: E402

OUT = os.path.join(HERE, 'out')
sd.ICON_DIR = os.path.join(OUT, 'icons')
C, RING = sd.C, sd.RING

ICONS = ['businessman', 'businesswoman', 'customer_support', 'multiple_devices', 'calculator', 'filing_cabinet',
         'services', 'electro_devices', 'privacy', 'inspection', 'mind_map', 'search', 'news', 'factory', 'data_sheet',
         'home', 'signature', 'todo_list', 'positive_dynamic', 'view_details', 'calendar', 'clock']
os.makedirs(sd.ICON_DIR, exist_ok=True)
for n in ICONS:
    path = os.path.join(sd.ICON_DIR, n + '.svg')
    if not os.path.exists(path):
        req = urllib.request.Request('https://cdn.jsdelivr.net/npm/flat-color-icons@1.1.0/svg/%s.svg' % n,
                                     headers={'User-Agent': 'icons-fetch'})
        with open(path, 'wb') as f:
            f.write(urllib.request.urlopen(req, timeout=30).read())

# =====================================================================
# 시스템 아키텍처: 계층 칸 + 아이콘 동그라미 + 라벨 붙은 화살표 + 범례
# =====================================================================
a = sd.Canvas(1800, 740)
a.tier(0, 0, 250, 440, '이용자')
a.tier(330, 0, 520, 440, '브라우저 (웹 화면)')
a.tier(890, 0, 500, 440, '서버 (API)')
a.tier(1430, 0, 370, 440, '생성형 AI')
a.tier(330, 480, 1470, 260, '데이터와 일괄 처리 (시설 정보를 모을 때 한 번)', title_dx=230)

# 이용자
a.node(125, 112, 'businessman', '시민', ['휴대폰, PC'], 'person', side='below')
a.node(125, 307, 'customer_support', '안내 창구 직원', ['창구 PC'], 'person', side='below', tsize=25)

# 브라우저
a.node(395, 110, 'multiple_devices', '화면', ['문장 입력, 결과 비교, 예약 연결'], 'person', r=48)
a.node(395, 275, 'calculator', '규칙 엔진', ['예약 가능 시간 판정', '거리와 요금 계산', '빠진 조건 질문'], 'rule')
a.node(395, 397, 'filing_cabinet', '브라우저 저장소', ['최근 조건, 로그인 없음'], 'data', r=36, tsize=25)

# 서버
a.node(955, 105, 'services', 'API', ['/api/extract (조건 추출)', '/api/explain (안내문)'], 'ai')
a.node(955, 240, 'electro_devices', 'LLM 연결부', ['개인정보 지우기, 모델 교체 가능'], 'ai')
a.badge('privacy', 955 + 36, 240 - 36, 30)
a.node(955, 378, 'inspection', '검증기', ['숫자, 시설 이름, 원문 대조'], 'ai')

# 생성형 AI
a.text(1450, 92, '설정만 바꿔 모델 교체', 21, 400, C['soft'], 'start')
a.node(1500, 240, 'mind_map', 'LLM', ['상용 모델 또는', '공개 모델'], 'ai', r=48)
a.node(1500, 375, 'search', '임베딩 모델', ['비슷한 시설 찾기'], 'ai', r=40)

# 데이터 띠 (오른쪽에서 왼쪽으로 흐름)
a.node(1500, 585, 'news', '공공시설 예약 정보', ['공공데이터 API', '시설별 이용 조건'], 'data', r=44, side='below')
a.node(955, 585, 'factory', '일괄 정리', ['이용 조건을 항목으로 정리', '시설끼리 비슷한 정도 계산'], 'ai', r=44,
       side='below')
a.badge('mind_map', 955 + 36, 585 - 36, 30)
a.node(480, 585, 'data_sheet', '정리된 시설 정보', ['조건과 원문 구절', '시설 분류 30개'], 'data', r=44, side='below')

# 범례
a.text(16, 516, '범례', 23, 700, C['ink'], 'start')
for i, (k, lab) in enumerate([('ai', '생성형 AI'), ('rule', '규칙 엔진 (숫자 계산)'), ('data', '데이터'),
                              ('person', '사람과 화면')]):
    fill, stroke, sw = RING[k]
    yy = 556 + i * 44
    a.circle(36, yy - 8, 15, fill, stroke, sw if k != 'rule' else 3.5)
    a.text(62, yy, lab, 22, 400, C['body'], 'start')

# 연결
a.arrow([(171, 112), (348, 112)])                          # 시민 → 화면
a.arrow([(171, 300), (300, 300), (300, 140), (352, 140)])  # 창구 직원 → 화면
a.arrow([(395, 158), (395, 229)], both=True)               # 화면 ↔ 규칙 엔진
a.arrow([(395, 321), (395, 361)])                          # 규칙 엔진 → 저장소
a.arrow([(838, 108), (909, 108)], '원하는 것', (858, 84))     # 화면 → API
a.arrow([(955, 151), (955, 194)])                          # API → 연결부
a.arrow([(955, 286), (955, 332)])                          # 연결부 → 검증기
a.arrow([(909, 378), (870, 378), (870, 136), (842, 136)], '통과분만', (862, 262))  # 검증기 → 화면
a.arrow([(1362, 240), (1452, 240)], both=True)             # 연결부 ↔ LLM
a.arrow([(1456, 585), (999, 585)])                         # 예약 정보 → 일괄 정리
a.arrow([(911, 585), (524, 585)])                          # 일괄 정리 → 정리된 정보
a.arrow([(436, 585), (310, 585), (310, 275), (349, 275)], '정리된 조건', (310, 462))  # → 규칙 엔진
a.save(os.path.join(OUT, 'architecture.svg'))

# =====================================================================
# 서비스 흐름: 예시 인물이 단계를 지나가는 여정
# (아이콘, 단계 이름, 이용자가 하는 일, AI나 규칙 엔진이 하는 일, 걸리는 시간)
# =====================================================================
steps = [
    ('home', '시작', '홈', ['예시로 먼저 보기', '또는 바로 입력'], ('rule', '예시 조건', '불러오기'), '10초'),
    ('signature', '원하는 것 적기', '1단계 입력', ['한 문장 입력', '(유일한 타이핑)'], ('ai', '조건 추출', '근거 확인'), '30초'),
    ('todo_list', '조건 확인', 'AI가 찾은 조건', ['날짜, 인원, 거리', '고치거나 확인'], ('rule', '빠진 조건', '질문하기'), '30초'),
    ('positive_dynamic', '결과 비교', '2단계 결과', ['정렬 바꿔 비교', '지도에서 보기'], ('rule', '예약 가능', '시간 판정'), '즉시'),
    ('view_details', '자세히 보기', '시설 상세', ['이용 조건 원문', '요금 확인'], ('ai', '조건 원문', '쉬운 말 안내'), '필요할 때'),
    ('calendar', '예약하기', '3단계 예약', ['예약 사이트로', '바로 이동'], ('rule', '예약 링크', '연결'), '1분'),
]
f = sd.Canvas(1800, 480)
X0, PY = 236, 108
S = (1800 - X0) / len(steps)
xs = [X0 + S * (i + 0.5) for i in range(len(steps))]

# 길
f.line([(150, PY), (xs[-1] + 60, PY)], C['path'], 12)
for i in range(len(xs) - 1):
    mx = (xs[i] + xs[i + 1]) / 2
    f.poly([(mx + 12, PY), (mx - 8, PY - 12), (mx - 8, PY + 12)], C['ailine'])

# 예시 인물
f.circle(100, 100, 74, C['ai'], C['ailine'], 3)
f.icon('businesswoman', 100, 100, 104)
f.text(100, 210, '예시 인물, 30대', 25, 700, C['ink'])
f.text(100, 238, '휴대폰으로 혼자', 22, 400, C['soft'])
f.rect(30, 258, 140, 40, C['blue'], None, 0, 20)
f.text(100, 286, '전체 3분', 24, 700, C['white'])
f.icon('customer_support', 100, 352, 56)
f.text(100, 410, '창구 직원과', 21, 700, C['ink'])
f.text(100, 436, '함께 써도 같은 화면', 21, 400, C['soft'])

for (ic, title, sub, user, (kind, s1, s2), t), cx in zip(steps, xs):
    f.circle(cx, PY, 56, C['white'], C['personline'], 2.5)
    f.icon(ic, cx, PY, 70)
    f.text(cx, 200, title, 27, 700, C['ink'])
    f.text(cx, 226, sub, 21, 400, C['soft'])
    f.text(cx, 262, user[0], 23, 400, C['body'])
    f.text(cx, 289, user[1], 23, 400, C['body'])
    fill, stroke, sw = RING[kind]
    cw = S - 26
    f.rect(cx - cw / 2, 308, cw, 70, fill, stroke, sw if kind != 'rule' else 3, 14)
    f.icon('mind_map' if kind == 'ai' else 'calculator', cx - cw / 2 + 30, 343, 36)
    tx = cx - cw / 2 + 56
    tcol = C['aitext'] if kind == 'ai' else C['ink']
    f.text(tx, 337, s1, 21, 600, tcol, 'start')
    f.text(tx, 363, s2, 21, 600, tcol, 'start')
    f.icon('clock', cx - 44, 411, 28)
    f.text(cx - 24, 419, t, 23, 700, C['ink'], 'start')

# 결과 말풍선 (결과 비교 단계)
bx = xs[3] + 40
f.rect(bx, 6, 168, 46, C['white'], C['green'], 2.5, 23)
f.poly([(bx + 18, 50), (bx + 34, 50), (bx + 12, 66)], C['green'])
f.text(bx + 84, 38, '가능한 곳 6곳', 21, 700, C['green'])

# 범례
ly = 466
f.rect(X0 + 10, ly - 22, 30, 26, RING['ai'][0], RING['ai'][1], 2.5, 8)
f.text(X0 + 50, ly, '생성형 AI가 하는 일', 21, 400, C['body'], 'start')
f.rect(X0 + 290, ly - 22, 30, 26, RING['rule'][0], RING['rule'][1], 3, 8)
f.text(X0 + 330, ly, '규칙 엔진이 하는 일 (숫자는 여기서만 나옴)', 21, 400, C['body'], 'start')
f.text(1792, ly, '타이핑은 원하는 것 적기 한 번뿐', 21, 600, C['blue'], 'end')
f.save(os.path.join(OUT, 'service-flow.svg'))
