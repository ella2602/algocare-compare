#!/usr/bin/env python3
"""GS SHOP 공유용 알고케어 뉴트리션 보틀 품질 비교 PDF 빌더.

- data/notion_bottles.md : Notion 페이지(40d9954b…)에서 추출한 비교표 원문
- 이 파일의 BOTTLES       : 페이지별 히어로 카피·핵심 포인트(노션 특징 문구 요약)
출력: deck.html → render.js 로 PDF 변환
"""
import html, re, pathlib

ROOT = pathlib.Path(__file__).parent
MD = (ROOT / "data" / "notion_bottles.md").read_text(encoding="utf-8")

# ---------------------------------------------------------------- 표 파싱
def parse_tables(md):
    """'## 제목' 단위로 첫 번째 '| 구분' 표를 리스트로 반환."""
    out = {}
    for sec in re.split(r"\n(?=## )", md):
        m = re.match(r"## (.+)", sec)
        if not m:
            continue
        lines = [l for l in sec.splitlines() if l.startswith("| ")]
        if not lines:
            continue
        rows = []
        for l in lines:
            cells = [c.strip() for c in l.strip().strip("|").split(" | ")]
            if set("".join(cells)) <= set("-: "):
                continue
            rows.append(cells)
        out[m.group(1).strip()] = rows
    return out

TABLES = parse_tables(MD)

def tbl(prefix):
    for k, v in TABLES.items():
        if k.startswith(prefix):
            return v
    raise KeyError(prefix)

LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

def cell_html(text):
    t = html.escape(text)
    t = LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    t = t.replace(" / ", "<br>")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<=\w)·(?=\w)", "·<wbr>", t)   # 균주 코드 등 긴 ·연결 문자열이 셀 밖으로 넘치지 않게 줄바꿈 허용
    return t

# ------------------------------------------------- 공식 제품명(위키 정본 기준)
OFFICIAL = {
    "알고케어 오메가3": "알고케어 뉴트리션 장용성 초임계 rTG 오메가3",
    "알고케어 프로바이오틱스": "알고케어 뉴트리션 프로바이오틱스",
    "알고케어 멜라토닌": "알고케어 뉴트리션 멜라토닌",
    "알고케어 코큐텐": "알고케어 뉴트리션 장용성 코큐텐",
    "알고케어 루테인지아잔틴": "알고케어 뉴트리션 장용성 루테인지아잔틴",
    "알고케어 시너지마그네슘": "알고케어 시너지 마그네슘",
    "알고케어 밀크씨슬": "알고케어 뉴트리션 밀크씨슬",
    "알고케어 바나바": "알고케어 뉴트리션 바나바",
    "알고케어 홍경천&테아닌": "알고케어 뉴트리션 홍경천&테아닌",
    "알고케어 멀티비타민미네랄": "알고케어 뉴트리션 멀티비타민미네랄",
    "알고케어 비타민D": "알고케어 뉴트리션 비타민D3",
    "알고케어 칼슘&마그네슘": "알고케어 뉴트리션 칼슘&마그네슘",
    "알고케어 보스웰리아": "알고케어 뉴트리션 보스웰리아",
    "알고케어 녹차카테킨": "알고케어 뉴트리션 녹차카테킨",
}
# 노션 제품 행이 이미 정식명이면 그대로 통과(OFFICIAL.get(c, c)) — 이중 매핑 없음

PHARMA_LABEL = "제약사 브랜드 인기 · 프리미엄 상품 (해외 제품 포함)"

# 표에서 인쇄물에 맞지 않는 행 라벨 정리
ROW_LABEL = {"판매 링크": "판매처"}

def render_table(rows, dense=False):
    # 글자 수가 매우 많은 표(멀티 8열 등)만 셀 여백을 줄여 자동 맞춤 글자 크기를 확보
    dense = sum(len(c) for r in rows for c in r) > 2600
    group_row, *body = rows
    ncol = len(group_row)
    # 알고케어 계열 열 판정: 그룹 라벨이 '알고케어'로 시작
    kinds = []
    cur = None
    for i, g in enumerate(group_row):
        if i == 0:
            kinds.append("label"); continue
        if g:
            cur = g
        if cur.startswith("알고케어"):
            kinds.append("algo-pre" if "출시 예정" in cur else "algo")
        elif cur.startswith("GS"):
            kinds.append("gs")
        else:
            kinds.append("pharma")
    # 그룹 헤더(colspan)
    groups = []
    for i, g in enumerate(group_row[1:], start=1):
        if g:
            groups.append([g, 1, kinds[i]])
        else:
            groups[-1][1] += 1
    h = [f'<table class="cmp{" dense" if dense else ""}">']
    h.append('<colgroup><col class="c-label">' + "".join(
        f'<col class="c-{k}">' for k in kinds[1:]) + "</colgroup>")
    h.append("<thead><tr><th class=\"corner\"></th>")
    for g, span, k in groups:
        label = g
        if k.startswith("algo"):
            label = g.replace(" (출시 예정)", "").replace(" (미국 출시 예정)", "")
            pre = "미국 출시 예정" if "미국" in g else ("출시 예정" if "출시 예정" in g else "")
            tag = f'<span class="tag">{pre}</span>' if pre else ""
            h.append(f'<th class="grp {k}" colspan="{span}">{html.escape(label)}{tag}</th>')
        else:
            if k == "pharma":
                label = PHARMA_LABEL
            h.append(f'<th class="grp {k}" colspan="{span}">{html.escape(label)}</th>')
    h.append("</tr>")
    # 제품명 행
    prod = body[0]
    h.append('<tr class="prod"><th class="rl">제품</th>')
    for i, c in enumerate(prod[1:], start=1):
        name = OFFICIAL.get(c, c)
        h.append(f'<th class="{kinds[i]}">{cell_html(name)}</th>')
    h.append("</tr></thead><tbody>")
    for r in body[1:]:
        lab = ROW_LABEL.get(r[0], r[0])
        h.append(f'<tr><th class="rl">{html.escape(lab)}</th>')
        for i, c in enumerate(r[1:], start=1):
            cls = kinds[i]
            plain = re.sub(r"\s+", "", c)
            if plain in ("-", "없음") or plain.startswith("(개발중)"):
                cls += " mute"
            h.append(f'<td class="{cls}">{cell_html(c)}</td>')
        h.append("</tr>")
    h.append("</tbody></table>")
    return "".join(h)

# ------------------------------------------------------------- 콘텐츠
# 핵심 포인트는 노션 「알고케어 제품의 특징」 문구를 사실 그대로 요약
BOTTLES = [
 dict(key="omega", no="01", en="OMEGA-3", table="1. 오메가3",
      name="알고케어 뉴트리션 장용성 초임계 rTG 오메가3", photo="omega", pillcap="rTG 소형 캡슐 377mg",
      hero="글로벌 프리미엄 프랑스 Polaris사,<br>rTG 80% 고순도를 장용성 캡슐에",
      stats=[("80", "%", "오메가3 농도"), ("377", "mg", "소형 캡슐 1알"), ("3 : 2", "", "EPA : DHA 함량 별도 관리")],
      points=[
        ("프랑스 Polaris 원료", "IFOS 5-Star 인증으로 순도·안전성·품질을 검증받은 프리미엄 오메가3 원료사", "polaris"),
        ("오메가3 농도 80%", "비교 제품 중 최상위(유한양행 제품과 동일). 그 외 제품은 60% 또는 농도 미표기"),
        ("rTG · 377mg 소형 캡슐", "1알 EPA+DHA 300mg. 2~3알로 식약처 기능성 용량(500·600·900mg)에 맞춰 섭취"),
        ("장용 캡슐 · EPA:DHA 함량 별도 관리", "어취와 더부룩함을 줄인 장용 캡슐. EPA 180 : DHA 120mg으로 쏜리서치 Super EPA와 같은 3:2"),
      ],
      core="Polaris 원료 · 농도 80% · rTG · EPA:DHA 함량 별도 관리, 네 가지를 모두 갖춘 유일한 제품"),
 dict(key="probio", no="02", en="PROBIOTICS", table="2. 프로바이오틱스",
      name="알고케어 뉴트리션 프로바이오틱스", photo="probio", pillcap="장용 캡슐 200mg",
      hero="일동바이오사이언스 국내 특허 균주 5종,<br>4중 코팅(Q-Shield®)에 장용성 캡슐까지",
      stats=[("500억 / 100억", "", "투입균수 / 보장균수"), ("5", "종", "특허 균주 IDCC"), ("4중+장용", "", "이중 보호 설계")],
      points=[
        ("일동바이오사이언스 특허 균주 5종", "한국인 대상 인체 적용 연구가 있는 IDCC 3201·4301·3302·2201·4101", "ildong"),
        ("보장균수 100억, 투입 500억", "보장균수의 5배를 투입. 투입 균수까지 확인 가능한 유일한 제품"),
        ("균체 4중 코팅 + 장용 캡슐", "위산을 지나 장까지 닿도록 이중 보호. 두 기술을 함께 갖춘 유일한 제품"),
        ("캡슐 수로 균수 조절", "높은 균수가 필요한 사람에게 영양설계 알고리즘에 따라 캡슐 수를 늘려 맞춤 조절"),
      ],
      core="특허 균주 · 투입 균수 표기 · 균체 코팅과 장용 캡슐 동시 적용"),
 dict(key="mela", no="03", en="MELATONIN", table="3. 멜라토닌",
      name="알고케어 뉴트리션 멜라토닌", photo="mela", pillcap="정제 · 1정 0.67mg",
      hero="0.67mg, 국내에 드문 저용량 설계로<br>나에게 맞추는 멜라토닌",
      stats=[("0.67", "mg", "1정 멜라토닌"), ("2", "mg↑", "국내 비교 제품 1회량"), ("단일", "", "멜라토닌 단일 배합")],
      points=[
        ("의도적인 1정 0.67mg 저용량", "사람마다 맞는 용량 편차가 큰 성분이라 개인별 맞춤을 위해 저용량으로 설계"),
        ("국내에서 드문 1mg 이하", "비교한 국내 제품은 모두 1회 2mg 이상 고정. 해외 Pure는 0.5mg 제품을 별도 운영"),
        ("정 수로 찾는 내 용량", "실제 알고케어 섭취자는 0.67~약 5mg 범위에서 정 수를 달리해 각자 맞는 양을 섭취 중"),
        ("멜라토닌 단일 배합", "국내 비교 3종은 모두 복합 배합. 테아닌·마그네슘 등은 알고케어 별도 보틀로 운영"),
      ],
      core="국내 비교군 중 저용량 멜라토닌으로 개인별 맞춤이 가능한 유일한 제품"),
 dict(key="sleep", no="03-1", en="SLEEP PRESTIGE", table="3-1.", prerelease=True,
      name="알고케어 프레스티지 수면", photo=None, badge="PRESTIGE",
      hero="멜라토닌 + 테아닌 200mg + GABA 50mg + Lactium®·Shoden®,<br>하나로 설계한 나이트 보틀",
      stats=[("5", "종", "핵심 성분 배합"), ("200", "mg", "테아닌 (Pure의 4배)"), ("300", "mg", "Lactium®")],
      points=[
        ("하나로 설계한 토탈 나이트 보틀", "멜라토닌 3mg + Lactium® 300mg + GABA 50mg + 테아닌 200mg + Shoden® 120mg"),
        ("Lactium® · Shoden® 배합", "인체 대상 수면 시험 결과가 있는 두 원료를 더함. 국내 비교 제품에는 없는 구성", "lactium"),
        ("테아닌 200mg", "허브 중심 배합인 Pure Best-Rest(테아닌 50mg)의 4배"),
      ],
      core="국내 비교 제품은 멜라토닌에 테아닌 · 트립토판 · 마그네슘 구성, 알고케어 프레스티지는 Lactium® · Shoden®까지"),
 dict(key="coq", no="04", en="COENZYME Q10", table="4. 코큐텐",
      name="알고케어 뉴트리션 장용성 코큐텐", photo="coq", pillcap="장용 연질캡슐 300mg",
      hero="장용성으로 완성한 Global Merchant사의 순도 98% 코큐텐",
      stats=[("장용", "", "연질캡슐 300mg"), ("98", "%", "고순도 · GMO-Free"), ("100~300", "mg", "1일 조절 범위")],
      points=[
        ("장용성 연질캡슐", "위장 편안함을 고려한 설계. 장용성 연질캡슐 제형을 갖춘 유일한 제품"),
        ("98% 고순도 코큐텐 단일 배합", "Global Merchant 98% GMO-Free 원료. 국내 비교 제품 3종은 비타민·미네랄 복합 배합"),
        ("국내 기능성 원료 유비퀴논", "국내 건강기능식품 기능성(항산화·높은 혈압 감소에 도움을 줄 수 있음)은 유비퀴논 형태만 인정"),
      ],
      core="유비퀴놀을 원하는 고객에게는 알고케어 USA 라인으로 Kaneka 유비퀴놀을 제안"),
 dict(key="coq-usa", no="04-1", en="COENZYME Q10 · USA", table=None, prerelease=True,
      name="(가칭) 알고케어 USA Vascular/Cardio Prime", photo=None, badge="USA",
      hero="Kaneka 유비퀴놀에 Pycnogenol®까지,<br>혈관 케어 프리미엄 보틀",
      stats=[("100", "mg", "Kaneka Ubiquinol®"), ("150", "mg", "Pycnogenol®"), ("4", "종", "활성형 B군")],
      points=[
        ("Kaneka Ubiquinol® 100mg", "미국 프리미엄 시장의 대표 유비퀴놀 원료. 쏜리서치 유비퀴놀과 같은 원료", "kaneka"),
        ("Pycnogenol® 150mg", "Horphag 피크노제놀을 더한 복합 설계"),
        ("활성형 B군", "엽산(Quatrefolic® 5-MTHF) · B6(P5P) · B2(R5P) · B12(메틸코발라민)"),
        ("미국용 · 국내 직구 고객용", "유비퀴놀 형태를 선호하는 해외 직구 고객층의 니즈를 반영한 설계"),
      ],
      core="미국 출시 예정 · 유비퀴놀에 혈관 건강 원료를 더한 복합 설계"),
 dict(key="lutein", no="05", en="LUTEIN & ZEAXANTHIN", table="5. 루테인",
      name="알고케어 뉴트리션 장용성 루테인지아잔틴", photo="lutein", pillcap="장용 연질캡슐 300mg",
      hero="Lute-gen® 개별인정형 원료로 매일 챙기는 눈 건강 기본 루틴",
      stats=[("10+2", "mg", "루테인 + 지아잔틴"), ("2", "캡슐", "최대 20+4mg까지"), ("장용", "", "연질캡슐 300mg")],
      points=[
        ("루테인 10 + 지아잔틴 2mg 단일 배합", "부담 없이 시작할 수 있는 눈 영양제 포지션"),
        ("개별인정형 Lute-gen® 원료", "Lute-gen®(Bio-gen Extracts)의 개별인정형 원료 사용", "lutegen"),
        ("최대 2캡슐까지 조절", "필요에 따라 루테인 20mg · 지아잔틴 4mg까지"),
        ("장용 연질캡슐", "위 부담을 덜어 주는 장용 연질캡슐을 갖춘 유일한 제품"),
      ],
      core="눈 피로 관리까지 원하는 고객에게는 프레스티지 라인을 제안"),
 dict(key="lutein-pre", no="05-1", en="EYE PRESTIGE", table=None, prerelease=True,
      name="알고케어 프레스티지 루테인지아잔틴", photo=None, badge="PRESTIGE",
      hero="Indena Mirtoselect® 빌베리와<br>아스타잔틴을 더한 프리미엄 눈 건강",
      stats=[("160", "mg", "Mirtoselect® 빌베리"), ("6", "mg", "아스타잔틴"), ("3", "가지", "기능성 함량 성분")],
      points=[
        ("황반 관리 + 눈 피로 관리", "루테인지아잔틴에 아스타잔틴 · 빌베리를 한 보틀에 담은 프레스티지 눈 케어 라인"),
        ("Indena Mirtoselect® 빌베리 160mg", "이탈리아 Indena의 빌베리를 개별인정형 기능성 함량으로 배합. 비교 제품 중 빌베리를 기능성 함량으로 넣은 제품 없음", "indena"),
        ("3가지 모두 기능성 함량", "루테인 · 아스타잔틴 · 빌베리를 모두 기능성 함량으로 갖춘 유일한 제품"),
      ],
      core="일동 마이니 · 고려은단은 루테인지아잔틴 + 아스타잔틴 2가지 배합"),
 dict(key="mag", no="06", en="MAGNESIUM", table="6. 마그네슘",
      name="알고케어 시너지 마그네슘", photo="mag", pillcap="미니정제 · 1정 Mg 25.71mg",
      hero="아쿠아민·젖산·글루콘산,<br>3종 마그네슘을 한 보틀에",
      stats=[("3", "종", "마그네슘 원료 복합"), ("25.71", "mg", "1정 단위 조절"), ("180~385", "mg", "1일 조절 범위")],
      points=[
        ("마그네슘 3종 복합 설계", "Aquamin(해조) + 젖산(유기산) + 글루콘산(유기산). 비교 제품은 원료 1종만 사용", "aquamin"),
        ("마그네슘 단일 배합", "그 밖의 성분 없이 멀티와 중복 섭취 방지. 국내 비교 3종은 칼슘·비타민D·B군 등 복합 배합"),
        ("1정 25.71mg 단위 조절", "180~385mg까지 조절. 국내 비교 제품은 1회 섭취량 고정(175~315mg)"),
      ],
      core="유기산 비중을 높인 프레스티지, 킬레이트 마그네슘 USA 라인까지"),
 dict(key="mag-line", no="06-1", en="MAGNESIUM · PRESTIGE & USA", table=None, prerelease=True,
      name="알고케어 프레스티지 마그네슘 · (가칭) 알고케어 USA Magnesium", photo=None, badge="PRESTIGE · USA",
      split=[
        dict(label="PRESTIGE", sub="알고케어 프레스티지 마그네슘 · 국내 출시 예정",
             hero="유기산 마그네슘 비중을 크게 높인 프레스티지 마그네슘",
             points=[
               ("유기산 마그네슘 50%", "흡수율이 좋은 것으로 알려진 유기산 마그네슘 비중을 50%로 (Mg 원소 기준)"),
               ("리포좀(메타좀) 마그네슘", "베이직 라인의 아쿠아민 대신 리포좀(메타좀) 마그네슘 사용"),
               ("유기산 비율 15% → 78%", "마그네슘 원료 중 유기산 마그네슘 비율, 베이직 대비 (원료 중량 기준)"),
             ]),
        dict(label="USA", sub="(가칭) 알고케어 USA Magnesium · 미국 출시 예정",
             hero="글로벌 킬레이트 원료사 Albion TRAACS® 비스글리시네이트, 킬레이트 마그네슘 200mg",
             points=[
               ("Albion TRAACS®", "세계적인 킬레이트 미네랄 원료사 Albion의 Magnesium Bisglycinate Chelate", "albion"),
               ("비스글리시네이트 단일 배합", "다른 형태를 섞지 않은 단일 배합 — 미국 프리미엄 마그네슘의 표준"),
               ("직구 고객 니즈 반영", "국내 규정상 킬레이트 마그네슘은 원료로 사용 불가. 해외 직구 수요에 대응"),
             ]),
      ]),
 dict(key="milk", no="07", en="MILK THISTLE", table="7. 밀크씨슬",
      name="알고케어 뉴트리션 밀크씨슬", photo="milk", pillcap="미니정제 · 1정 실리마린 43.33mg",
      hero="글로벌 프리미엄 허브 이탈리아 원료사<br>Indena의 밀크씨슬",
      stats=[("60", "%", "실리마린 순도"), ("130", "mg", "1일 실리마린 (기능성 함량)"), ("43.33", "mg", "1정 실리마린")],
      points=[
        ("Indena(이탈리아) 원료", "세계적인 허브 추출물 원료사 Indena의 순도 60% 밀크씨슬", "indena"),
        ("실리마린 130mg", "식약처 기능성 함량에 맞춘 설계 (비교 제품도 모두 130mg)"),
        ("1정 43.33mg 단위 맞춤", "개인별 미량 맞춤 가능. 비교 제품은 1알 130mg으로 1회 복용량 고정"),
        ("밀크씨슬 단일 배합", "그 밖의 성분 없이 멀티와 중복 섭취 방지. 국내 비교 3종은 비타민 B군 등 복합 배합"),
      ],
      core="실리마린 130mg은 같아도, 정 단위로 나눠 맞춤이 가능한 유일한 제품"),
 dict(key="banaba", no="08", en="BANABA", table="8. 바나바",
      name="알고케어 뉴트리션 바나바", photo="banaba", pillcap="미니정제",
      hero="혈당 건강이 필요할 때,<br>루틴에 더하는 STAR HI사 바나바 단일 보틀",
      stats=[("1.3", "mg", "코로솔산"), ("30", "μg", "크롬 최소 배합"), ("2", "종", "코로솔산 + 크롬만")],
      points=[
        ("필요한 사람에게만 더하는 보틀", "알고케어 사용자 중 혈당 관리가 필요한 사람에게 맞춤으로 더함"),
        ("코로솔산 1.3mg + 크롬 30μg", "식약처 기능성 함량만 담은 최소 배합. 비타민 · 미네랄은 멀티와 중복 섭취 방지"),
        ("비교 제품은 복합 배합", "비교 제품 4종은 B군 · 아연 · 셀렌 등 비타민 · 미네랄을 함께 배합"),
      ],
      core="알고케어 시스템 안에서 중복 없이 맞춤으로 더하는 보틀"),
 dict(key="rhod", no="09", en="RHODIOLA & THEANINE", table="9. 홍경천",
      name="알고케어 뉴트리션 홍경천&테아닌", photo="rhod", pillcap="미니정제",
      hero="스트레스 관리에 집중한<br>홍경천·테아닌 보틀",
      stats=[("200", "mg", "홍경천 추출물"), ("200", "mg", "L-테아닌"), ("4.2", "mg", "로사빈")],
      points=[
        ("홍경천 + 테아닌 한 보틀", "비교 제품 중 둘을 함께 담은 제품은 모어네이처와 알고케어 2종뿐"),
        ("홍경천 200mg · L-테아닌 200mg", "홍경천은 스페인 Nektium, 테아닌은 인도 Molecules bio labs 원료", "nektium"),
        ("두 성분 외 배합 없음", "마그네슘 · 비타민B군 · 아연은 알고케어 별도 보틀로 제공해 중복 섭취 방지"),
      ],
      core="여에스더 · 동아 · 종근당은 홍경천 없는 테아닌 중심 제품"),
 dict(key="multi", no="10", en="MULTIVITAMIN & MINERAL", table="10. 멀티",
      name="알고케어 뉴트리션 멀티비타민미네랄", photo="multi", pillcap="미니정제 120mg",
      hero="DSM·MenaQ7® 등 글로벌 원료사를 담은<br>데일리 밸런스 멀티",
      stats=[("21", "종", "비타민 13 · 미네랄 8"), ("40", "%", "지용성 A · E · K 기준치"), ("4~15", "정", "고객별 1일 섭취 범위")],
      points=[
        ("필요한 만큼 다르게, 차등 설계", "B1 · B12 1,000%로 높이고 지용성 A · E · K 40%, 비타민D 60%, 미량미네랄 60~80%"),
        ("DSM 비타민 10종 · MenaQ7® K2", "DSM(A · B군 5종 · C · D · E · K1), 이탈리아 Gnosis MenaQ7®, 미국 Jost Chemical 미네랄", "dsm"),
        ("중성 비타민C · K1+K2", "위장관 부담까지 고려한 L-아스코브산칼슘. 국내 비교 제품 중 MenaQ7® K2를 갖춘 유일한 제품"),
        ("칼슘 · 마그네슘은 별도 보틀", "시너지 마그네슘 · 칼슘&마그네슘 보틀로 나눠 중복 섭취 방지. 120mg 미니정제로 정 수 조절"),
      ],
      core="충족형(100%)도 고함량형(수천%)도 아닌 차등 설계 — 지용성 A · E · K 40%, 정 수 맞춤 조절까지"),
 dict(key="multi-line", no="10-1", en="MULTI · PRESTIGE & USA", table=None, prerelease=True,
      name="알고케어 프레스티지 멀티비타민미네랄 · (가칭) 알고케어 USA Essential Mineral Multi", photo=None, badge="PRESTIGE · USA",
      split=[
        dict(label="PRESTIGE", sub="알고케어 프레스티지 멀티비타민미네랄 · 출시 예정",
             hero="Quatrefolic® 활성형 엽산·메타좀 비타민C·헴철, 한 단계 위의 프리미엄 멀티",
             points=[
               ("활성형 엽산 · 메타좀 비타민C · 헴철", "국내 비교 제품 중 활성형 엽산 · 메타좀 비타민C를 사용한 멀티는 없음"),
               ("비타민D 1,000IU · B군 고함량", "D 250%로 별도 비타민D 보틀 없이. B1 · B2 50mg, B12 500㎍"),
               ("B6 · 지용성 A · K는 보수적으로", "고함량 장기 섭취 시 주의가 필요한 B6는 보수적으로, A · K는 베이직처럼 40%"),
             ]),
        dict(label="USA", sub="(가칭) 알고케어 USA Essential Mineral Multi · 미국 출시 예정",
             hero="Albion TRAACS® 킬레이트 미네랄과 Quatrefolic® 활성형 엽산, 글로벌 프리미엄 기준에 맞춘 멀티",
             points=[
               ("Albion TRAACS® 킬레이트 미네랄 7종", "국내 건강기능식품 규정상 쓸 수 없는 킬레이트 미네랄을 미국용 라인에 적용", "albion"),
               ("활성형 엽산 · 활성형 B군", "Quatrefolic® 5-MTHF, 메틸코발라민 · P5P · R5P"),
               ("비타민 · 미네랄 22종", "붕소 포함 22종, 철 · 칼슘 제외. 쏜리서치 수준의 프리미엄 품질"),
             ]),
      ]),
 dict(key="vitd", no="11", en="VITAMIN D3", table="11. 비타민D",
      name="알고케어 뉴트리션 비타민D3", photo="vitd", pillcap="미니정제 95mg · 1정 1,000IU",
      hero="DSM Quali®-D, 1,000IU부터 4,000IU까지<br>나에게 맞추는 비타민D",
      stats=[("1,000", "IU", "1정 비타민D3"), ("1~4", "정", "1,000~4,000IU 조절"), ("95", "mg", "미니정제 1정")],
      points=[
        ("1정 1,000IU, 정 수로 조절", "청소년 · 임산부 · 고령자 등 필요에 따라 1,000~4,000IU. 국내 · GS 비교 제품은 1정(캡슐) 고정"),
        ("DSM Quali®-D 원료", "국내 비타민D 표준 원료. 국내 비교 제품도 모두 DSM 원료 사용", "dsm"),
        ("95mg 미니정제", "중량이 확인되는 비교 제품은 280~600mg (캡슐 · 츄어블)"),
        ("고함량도 여러 알로", "쏜리서치는 1,000 · 4,000 · 10,000IU 등 SKU를 나눠 운영, 알고케어는 5.1mm 미니정제 여러 알로 맞춤"),
      ],
      core="1,000IU 단위 정 수 조절과 단일 배합을 함께 갖춘 유일한 제품"),
 dict(key="calmag", no="12", en="CALCIUM & MAGNESIUM", table="12. 칼슘",
      name="알고케어 뉴트리션 칼슘&마그네슘", photo="calmag", pillcap="미니정제 135mg",
      hero="칼슘:마그네슘 2:1,<br>체내 미네랄 균형을 고려한 칼슘 마그네슘 복합보틀",
      stats=[("2 : 1", "", "칼슘 : 마그네슘"), ("300+150", "mg", "1일 14정 기준"), ("23", "정", "최대 조절 (칼슘 약 493mg)")],
      points=[
        ("칼슘 : 마그네슘 2 : 1", "흡수에 좋은 비율로 알려진 2:1 설계. 종근당 칼슘 앤 마그네슘 · 아임비타와 같은 비율"),
        ("1정 칼슘 21.43 · 마그네슘 10.71mg", "1일 14정 기준, 최대 23정까지 정 수로 조절. 비교 제품은 1일 2정 또는 3캡슐 고정"),
        ("칼슘 · 마그네슘 단일 배합", "비타민D · K · 아연은 멀티 · 비타민D 보틀에 있어 중복 섭취 방지. 국내 비교 제품은 복합 배합"),
        ("해조칼슘 Aquamin F · 산화마그네슘", "역가가 높아 국내 칼마의 표준인 원료. 해조칼슘 Microferm(영국), 산화마그네슘 CALMAGS(독일)", "aquamin"),
      ],
      core="칼슘 · 마그네슘을 정 수로 조절 가능한 유일한 단일 배합 제품"),
 dict(key="boswellia", no="13", en="BOSWELLIA", table="13. 보스웰리아",
      name="알고케어 뉴트리션 보스웰리아", photo="boswellia", pillcap="미니정제 90mg",
      hero="식약처 개별인정형 원료 SERRATRIN®으로<br>만든 보스웰리아",
      stats=[("400", "mg", "1일 보스웰리아 추출물"), ("32.8", "mg", "AKBA + KBA"), ("90", "mg", "미니정제 1정 · 1일 8정")],
      points=[
        ("개별인정형 SERRATRIN®", "인도 Laila Nutraceuticals 원료, 지표성분 AKBA+KBA 82mg/g 표준화. 종근당 보스웰리아 7Days와 같은 원료", "laila"),
        ("보스웰리아 단일 배합", "비타민D · 아연 · 셀렌 등은 멀티에 있어 중복 섭취 방지. 비교 제품 중 단일 배합은 알고케어 · Pure뿐"),
        ("관절 건강 기능성", "관절 및 연골 건강에 도움을 줄 수 있음 — 국내 비교 3종과 같은 기능성의 건강기능식품"),
        ("90mg 미니정제 8정", "한 알 크기 부담이 적음. 국내 비교 제품은 800~900mg대 정제 1~2정"),
      ],
      core="식약처 인정 원료 SERRATRIN®을 다른 성분 없이 담은 유일한 국내 건강기능식품"),
 dict(key="catechin", no="14", en="GREEN TEA CATECHIN", table="14. 녹차",
      name="알고케어 뉴트리션 녹차카테킨", photo="catechin", pillcap="미니정제 100mg · 1정 카테킨 42.86mg",
      hero="체지방 관리가 필요할 때,<br>루틴에 더하는 UNIAREA사 녹차카테킨 단일 보틀",
      stats=[("300", "mg", "1일 카테킨 (7정)"), ("42.86", "mg", "1정 카테킨"), ("70", "%", "카테킨 표준화 원료")],
      points=[
        ("녹차추출물 단일 배합", "바나바 · 멀티비타민미네랄 보틀과 중복 섭취를 막으려고 코로솔산 · 비타민 · 미네랄을 넣지 않음"),
        ("카테킨 70% · EGCG 45~55%", "표준화한 녹차추출물 원료 사용 (미국 UNIAREA)"),
        ("5.1mm 미니정제 7정", "1정 42.86mg 단위. 국내 비교 제품은 1~2정 고정 섭취"),
        ("비교 제품은 복합 배합", "국내 비교 3종은 코로솔산 · B군 · 비타민C · 셀렌 등을 함께 배합"),
      ],
      core="녹차카테킨만 담아, 바나바 · 멀티와 중복 없이 더하는 보틀"),
]

LOGO_BLACK = (ROOT / "assets" / "algocare.svg").read_text().replace("#FAF9F9", "#0A0909")
LOGO_WHITE = (ROOT / "assets" / "algocare.svg").read_text()

def logo(dark=False, h=14):
    svg = LOGO_WHITE if dark else LOGO_BLACK
    return svg.replace('width="98" height="22"', f'height="{h}" width="{h*98/22:.1f}"', 1)

PAGE_NO = [0]

def footer(dark=False, src=True):
    PAGE_NO[0] += 1
    note = "자료 기준 2026.11.04" if src else ""
    return (f'<footer class="ft"><span class="ft-logo">{logo(dark, 11)}</span>'
            f'<span class="ft-note">{note}</span><span class="ft-no">{PAGE_NO[0]:02d}</span></footer>')

def stats_html(stats):
    return '<div class="stats">' + "".join(
        f'<div class="stat"><div class="sv">{html.escape(v)}<small>{html.escape(u)}</small></div>'
        f'<div class="sl">{html.escape(l)}</div></div>' for v, u, l in stats) + "</div>"

# 원료사 로고(공식 마크 원본 · 출처는 img/logos/SOURCES.md). 포인트 튜플의 3번째 값(키 또는 키 튜플)로 지정
# key: (파일, 높이 mm — 워드마크/심벌 비율 차이를 눈으로 맞춘 값, 대체 텍스트)
LOGOS = {   # 4번째 값: 밝은 색 마크를 다른 로고와 같은 회색 농도로 맞추는 보정(필터) — 형태·비율은 원본 그대로
    "polaris": ("polaris.png", 3.6, "Polaris", "dark"),
    "ildong":  ("ildong.png", 2.8, "Ildong Bioscience", "dark"),
    "lactium": ("lactium.png", 5.6, "Lactium", ""),
    "kaneka":  ("kaneka.svg", 5.0, "Kaneka Nutrients", "dark"),
    "lutegen": ("lutegen.png", 6.2, "Lute-gen", "dark"),
    "indena":  ("indena.svg", 4.4, "Indena", ""),
    "aquamin": ("aquamin.png", 5.4, "Aquamin", "soft"),
    "albion":  ("albion.svg", 5.0, "Albion Minerals", ""),
    "nektium": ("nektium.png", 3.4, "Nektium", ""),
    "dsm":     ("dsm.svg", 2.6, "dsm-firmenich", ""),
    "laila":   ("laila.png", 6.8, "Laila Nutra", "dark"),
}

def logos_html(keys):
    if not keys:
        return ""
    if isinstance(keys, str):
        keys = (keys,)
    imgs = "".join(f'<img class="{LOGOS[k][3]}" src="img/logos/{LOGOS[k][0]}" alt="{html.escape(LOGOS[k][2])}" style="height:{LOGOS[k][1]}mm">'
                   for k in keys if k in LOGOS)
    return f'<span class="pt-logo">{imgs}</span>' if imgs else ""

def points_html(points, cols=2):
    return f'<div class="points cols{cols}">' + "".join(
        f'<div class="pt"><div class="pt-n">{i:02d}</div><div><h4><span class="pt-t">{html.escape(p[0])}</span>{logos_html(p[2] if len(p) > 2 else None)}</h4>'
        f'<p>{html.escape(p[1])}</p></div></div>'
        for i, p in enumerate(points, 1)) + "</div>"

# ---------------------------------------------- 히어로 비주얼 시안 (VISUAL=duo|lens|studio)
# 기본값 classic = 기존 디자인(보틀 사진 + 우하단 알약 썸네일). 시안은 VISUAL 환경변수로만 켜짐.
import os
DEFAULT_VISUAL = "duo"   # 2026-11-04 사용자 선택: A안(duo) + 실물 크기 알약
VISUAL = os.environ.get("VISUAL", DEFAULT_VISUAL)
SUFFIX = "" if VISUAL == DEFAULT_VISUAL else f"_{VISUAL}"

# 실물 크기(1:1) 알약 — 1일 섭취 알 수: algocare-bottle-info 스킬 references/bottle-spec-and-dosage.md 「허가서상 1일 섭취량」
# 치수 출처: 정제 5.1mm 구형 = 같은 문서 제형 열 · 노션 위키 「알고케어 영양제 3D 렌더 기준」(지름 확인)
#           #3 경질캡슐 15.9×5.8mm = 위키 값(3호 기준) + 업계 규격표(Lonza Vcaps Ø5.57/5.83mm, 닫힌 길이 15.7~15.9mm)
#           연질캡슐 OV 7.5 약 12.6×7.6mm = 업계 표준(ChinaHealthSource 소프트젤 몰드 표 7.5 Oval 0.38~0.46mL, TES/Technophar 표 6.2~7.5 minims). 길이 12.6mm에 맞춤
#           연질캡슐 OV2 = mm 출처 없음 → 캡션 '확인 중', 눈금자 생략 (렌더 크기는 위키 추정 10.5mm)
PILLSPEC = {  # key: (1일 알 수, 종류, 길이 mm, 확정 여부)
    "multi": (6, "tab", 5.1, True), "rhod": (6, "tab", 5.1, True), "milk": (3, "tab", 5.1, True),
    "vitd": (1, "tab", 5.1, True), "banaba": (1, "tab", 5.1, True), "mag": (7, "tab", 5.1, True),
    "calmag": (14, "tab", 5.1, True), "catechin": (7, "tab", 5.1, True), "boswellia": (8, "tab", 5.1, True),
    "mela": (3, "tab", 5.1, True),
    "omega": (3, "soft", 12.6, True), "coq": (1, "soft", 12.6, True), "lutein": (1, "soft", 12.6, True),
    "probio": (1, "hard", 15.9, True),
}

def real_pills(k):
    n, kind, L, ok = PILLSPEC[k]
    gap = 1.5 if kind == "tab" else 2.2
    per = n if n <= 8 else -(-n // 2)
    if kind == "hard":   # 자사몰 실물은 흰 캡슐, Drive 누끼(노란 정제)는 불일치 → 중립 실루엣
        one = f'<i class="rp-hard" style="width:{L}mm;height:5.8mm"></i>'
    else:
        one = f'<img class="rp" src="img/cut/{k}_pill11.png" style="width:{L}mm">'
    pills = f'<div class="rp-row" style="width:{per * (L + gap):.2f}mm;gap:{gap}mm {gap}mm">' + one * n + "</div>"
    unit = "정" if kind == "tab" else "캡슐"
    if kind == "tab":
        cap = f"실물 크기 · Ø5.1mm · 1일 {n}{unit}"
    elif kind == "hard":
        cap = f"실물 크기 · 15.9×5.8mm · 1일 {n}{unit}"
    elif ok:
        cap = f"실물 크기 · 약 12.6×7.6mm · 1일 {n}{unit}"
    else:
        cap = f"1일 {n}{unit} · 캡슐 실측 치수 확인 중"
    scale = ('<div class="rp-scale"><i></i><span>0</span><span>10mm</span></div>' if ok else "")
    return f'<div class="vd-real">{pills}{scale}<div class="vd-cap"><span>{"ACTUAL SIZE · 1:1" if ok else "DAILY SERVING"}</span><b>{cap}</b></div></div>'

def photo_visual(b):
    bt = f'background-image:url(img/{b["photo"]}_bottle.jpg)'
    pl = f'background-image:url(img/{b["photo"]}_pill.jpg)'
    cap = html.escape(b.get("pillcap", ""))
    if VISUAL == "duo":      # A. 세로 2단: 보틀 + 알약 매크로 스트립, 같은 톤·같은 캡션 체계
        nm = b["name"]
        for pre in ("알고케어 뉴트리션 ", "알고케어 "):
            if nm.startswith(pre):
                brand, prod = pre.strip(), nm[len(pre):]; break
        else:
            brand, prod = "알고케어", nm
        label = (f'<div class="vd-name"><span>{html.escape(brand)}</span>'
                 f'<b>{html.escape(prod)}</b></div>')
        return (f'<div class="visual v-duo"><div class="vd-top" style="{bt}">{label}</div>'
                f'<div class="vd-bot">{real_pills(b["photo"])}</div></div>')
    if VISUAL == "lens":     # B. 보틀 전면 + 원형 매크로 렌즈, 리더 라인과 캡션으로 보틀에 연결
        return (f'<div class="visual v-lens" style="{bt}"><div class="vl-line"></div>'
                f'<figure class="vl-fig"><div class="vl-lens" style="{pl}"></div>'
                f'<figcaption><span>1 UNIT · ACTUAL</span>{cap}</figcaption></figure></div>')
    if VISUAL == "studio":   # C. 단일 구성 패널: 같은 프레임의 보틀 카드 + 알약 카드 + 캡션
        return (f'<div class="visual v-studio"><div class="vs-card vs-bottle" style="{bt}"></div>'
                f'<div class="vs-row"><div class="vs-card vs-pill" style="{pl}"></div>'
                f'<div class="vs-cap"><span>{b["no"]} · {html.escape(b["en"])}</span><b>{cap}</b>'
                f'<i>보틀 속 한 알</i></div></div></div>')
    if VISUAL == "scene":    # D. 단일 연출 장면: Drive 보틀 누끼 + 바닥의 알약 누끼 3~5알, 공통 접지 그림자·반사
        return scene_visual(b)
    raise ValueError(VISUAL)

import json
CUT = ROOT / "img" / "cut"
CUTMETA = json.loads((CUT / "meta.json").read_text()) if (CUT / "meta.json").exists() else {}
# 알약 배치 (중심 x mm, 바닥 y mm, 크기 mm, 회전) — 모든 보틀 공통
SCENE_PILLS = [(22, 187, 21, -14), (81, 181, 16, 18), (12, 166, 10, 32), (67, 167, 11.5, -24), (90, 161, 7, 6)]
SCENE_FALLBACK = {"probio": "photo"}   # 보틀 누끼 없음 + Drive 알약 누끼가 자사몰 실물(흰 캡슐)과 달라 자사몰 보틀 사진 사용

def _rgba(hexc, a):
    h = hexc.lstrip("#"); return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

def scene_visual(b):
    k = b["photo"]; m = CUTMETA.get(k, {})
    tint = m.get("tint", "#d8d0c6")
    style = f'--tint:{_rgba(tint, .20)};--tint2:{_rgba(tint, .08)}'
    cap = f'<div class="sc-cap">{html.escape(b.get("pillcap", ""))}</div>'
    pill = f"img/cut/{k}_pill.png"
    pr = m.get("pill_ratio", 1)
    def pills(spec):
        out = []
        for i, (x, y, sz, rot) in enumerate(spec):
            w = sz * min(pr, 1) if pr < 1 else sz; h = w / pr * .8
            out.append(f'<div class="sc-p d{i}" style="left:{x - w/2:.1f}mm;top:{y - h:.1f}mm;width:{w:.1f}mm;height:{h:.1f}mm">'
                       f'<img src="{pill}" style="transform:rotate({rot}deg)"></div>')
        return "".join(out)
    if (CUT / f"{k}_bottle.png").exists():
        bw = 112 * m["ratio"]
        bot = (f'<div class="sc-bottle" style="left:{(104 - bw)/2:.1f}mm;width:{bw:.1f}mm">'
               f'<img class="sc-b" src="img/cut/{k}_bottle.png"><img class="sc-r" src="img/cut/{k}_bottle.png"></div>'
               f'<div class="sc-shadow"></div>')
        return f'<div class="visual v-scene" style="{style}"><div class="sc-floor"></div>{bot}{pills(SCENE_PILLS)}{cap}</div>'
    if SCENE_FALLBACK.get(k) == "photo" or not (CUT / f"{k}_pill.png").exists():
        return (f'<div class="visual v-scene sc-photo" style="{style}"><div class="sc-ph" '
                f'style="background-image:url(img/{k}_bottle.jpg)"></div>{cap}</div>')
    # 보틀 누끼가 없는 보틀: 알약 하나를 크게 세운 같은 장면 (pill-only)
    big = 56 if pr >= .8 else 44
    hw = big * (pr if pr < 1 else 1); hh = hw / pr
    hero = (f'<div class="sc-hero" style="left:{(104 - hw)/2:.1f}mm;top:{150 - hh:.1f}mm;width:{hw:.1f}mm;height:{hh:.1f}mm">'
            f'<img class="sc-b" src="{pill}"><img class="sc-r" src="{pill}"></div><div class="sc-shadow sm"></div>')
    return (f'<div class="visual v-scene sc-pillonly" style="{style}"><div class="sc-floor"></div>{hero}'
            f'{pills([SCENE_PILLS[0], SCENE_PILLS[1], SCENE_PILLS[2], SCENE_PILLS[4]])}{cap}</div>')

KEY_TOP = "ALL"   # KEY 박스를 수치 바로 아래(포인트 위)로 올림. "ALL" 또는 보틀 key 집합

def hero_page(b):
    pre = b.get("prerelease")
    if b.get("photo") and VISUAL != "classic":
        visual = photo_visual(b)
    elif b.get("photo"):
        visual = (f'<div class="visual photo" style="background-image:url(img/{b["photo"]}_bottle.jpg)">'
                  f'<div class="pill" style="background-image:url(img/{b["photo"]}_pill.jpg)"></div></div>')
    else:
        visual = (f'<div class="visual dark"><div class="vd-in"><div class="vd-badge">{b["badge"]}</div>'
                  f'<div class="vd-en">{b["en"]}</div><div class="vd-rule"></div>'
                  f'<div class="vd-sub">{"미국 출시 예정" if "USA" in b["badge"] and "PRESTIGE" not in b["badge"] else "출시 예정"}</div></div>'
                  f'<div class="vd-logo">{logo(True, 13)}</div></div>')
    if b.get("split"):
        body = '<div class="split">' + "".join(
            f'<div class="sp"><div class="sp-lab">{s["label"]}</div><div class="sp-sub">{html.escape(s["sub"])}</div>'
            f'<h3 class="sp-hero">{s["hero"]}</h3>{points_html(s["points"], 1)}</div>' for s in b["split"]) + "</div>"
        content = (f'<div class="eyebrow"><b>{b["no"]}</b><span>{b["en"]}</span><em>출시 예정</em></div>'
                   f'<div class="pname">{html.escape(b["name"])}</div>{body}')
    else:
        content = (f'<div class="eyebrow"><b>{b["no"]}</b><span>{b["en"]}</span>{"<em>출시 예정</em>" if pre else ""}</div>'
                   + ("" if (VISUAL == "duo" and b.get("photo")) else f'<div class="pname">{html.escape(b["name"])}</div>') +
                   f'<h1 class="hero">{b["hero"]}</h1>'
                   f'{stats_html(b["stats"])}'
                   + (f'<div class="core-wrap top"><div class="core"><span>KEY</span>{html.escape(b["core"])}</div></div>'
                      f'{points_html(b["points"])}' if (KEY_TOP == "ALL" or b["key"] in KEY_TOP) else
                      f'{points_html(b["points"])}'
                      f'<div class="core-wrap"><div class="core"><span>KEY</span>{html.escape(b["core"])}</div></div>'))
    return f'<section class="page hp">{visual}<div class="content">{content}</div>{footer()}</section>'

def table_page(b, rows, title_extra=""):
    ncols = len(rows[0])
    dense = ncols >= 7
    return (f'<section class="page tp"><header class="tp-h"><div class="eyebrow"><b>{b["no"]}</b><span>{b["en"]}</span><i>COMPARISON</i></div>'
            f'<h2>{html.escape(b["name"])}{title_extra} <span>vs 비교 제품</span></h2></header>'
            f'<div class="tp-body">{render_table(rows, dense)}</div>'
            f'<div class="legend"><span class="lg algo"></span>알고케어 '
            + ('<span class="lg algo-pre"></span>알고케어 출시 예정 ' if any("출시 예정" in g for g in rows[0]) else '') +
            f'<span class="lg gs"></span>GS SHOP 매칭 상품 <span class="lg pharma"></span>{PHARMA_LABEL}'
            f'<span class="lg-note">「-」 미표기 · 미확인 / 「없음」 해당 성분 없음</span></div>{footer()}</section>')

COVER = os.environ.get("COVER", "pills")   # dark: 오메가3·바나바 다크 연출컷 / pills: 알약 원형 배치(룩북)

def cover():
    img = {"dark": "cover_dark", "pills": "cover_pills"}[COVER]
    return (f'<section class="page cover cv-{COVER}"><div class="cv-photo" style="background-image:url(img/{img}.jpg)"></div>'
            f'<div class="cv-top">{logo(COVER == "dark", 20)}<span>내부용 / 대외비 · 2026.11</span></div>'
            f'<div class="cv-main"><div class="cv-kicker">ALGOCARE NUTRITION BOTTLE</div>'
            f'<h1>알고케어 뉴트리션 보틀<br><b>품질 비교 자료</b></h1>'
            f'<div class="cv-rule"></div><div class="cv-meta">14 BOTTLES · 2026.11</div></div></section>')

def lineup(appendix=None):
    rows = []
    for b in BOTTLES:
        if b.get("split"):
            for s in b["split"]:
                rows.append((b["no"], s["sub"].split(" · ")[0], s["hero"], True))
        else:
            rows.append((b["no"], b["name"], b["hero"].replace("<br>", " "), b.get("prerelease")))
    items = "".join(
        f'<div class="lu{" pre" if pre else ""}"><div class="lu-no">{no}</div><div class="lu-tx">'
        f'<div class="lu-nm">{html.escape(nm)}{"<em>출시 예정</em>" if pre else ""}</div>'
        f'<div class="lu-hero">{hero}</div></div></div>'
        for no, nm, hero, pre in rows)
    if appendix:   # 상세판: 본문 뒤 APPENDIX가 있음을 라인업(목차)에서 알림
        items += (f'<div class="lu lu-ax"><div class="lu-no">별첨]</div><div class="lu-tx">'
                  f'<div class="lu-nm">APPENDIX · p.{appendix[0]:02d}–{appendix[1]:02d}<span class="ax-sub">보틀별 상세 비교 정보</span></div>'
                  f'</div></div>')
        rows = rows + [None]
    return (f'<section class="page lineup"><header class="tp-h">'
            f'<h2>알고케어 뉴트리션 보틀 품질 비교 자료 목차</h2></header><div class="lu-grid{" dense" if len(rows) > 14 else ""}" style="grid-template-rows:repeat({(len(rows)+1)//2},1fr)">{items}</div>{footer()}</section>')

def closing():
    pillars = [
        ("SOURCE", "글로벌 프리미엄 원료를 씁니다", "Polaris · Indena · DSM · Gnosis MenaQ7® · Laila SERRATRIN® · 일동바이오사이언스 — 성분마다 검증된 프리미엄 원료사 원료 사용"),
        ("DOSE", "미니정제 알 수 조절로 개인별 맞춤 실현", "오메가3 · 멜라토닌 · 비타민D · 칼슘&마그네슘까지, 고정 1회분이 아닌 정 · 캡슐 단위 조절"),
        ("SYSTEM", "설계 단계부터 중복 섭취를 막습니다", "단일 배합 보틀로 멀티비타민미네랄과의 중복 섭취를 막는 알고케어 시스템"),
    ]
    cards = "".join(f'<div class="pl"><div class="pl-en">{e}</div><h3>{t}</h3><p>{html.escape(d)}</p></div>' for e, t, d in pillars)
    return (f'<section class="page closing"><div class="cl-in"><div class="cv-kicker">WHY ALGOCARE</div>'
            f'<h1>같은 이름의 영양제라도,<br><b>설계는 다릅니다.</b></h1><div class="pillars">{cards}</div></div>'
            f'<div class="cl-logo">{logo(True, 22)}</div></section>')

CSS = (ROOT / "deck.css").read_text(encoding="utf-8") + (ROOT / "visual_options.css").read_text(encoding="utf-8")

pages = [cover(), lineup()]
for b in BOTTLES:
    pages.append(hero_page(b))
    if b["table"]:
        pages.append(table_page(b, tbl(b["table"])))
pages.append(closing())

doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>알고케어 뉴트리션 보틀 품질 비교 자료</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>{CSS}</style></head><body>{''.join(pages)}<script>
function fit(box, el, lo, hi, unit){{ // el 글자 크기를 box 안에 들어가는 최대값으로
  let a=lo,b=hi;
  for(let i=0;i<14;i++){{const m=(a+b)/2; el.style.fontSize=m+unit;
    if(box.scrollHeight>box.clientHeight+0.5 || el.getBoundingClientRect().bottom>box.getBoundingClientRect().bottom+0.5) b=m; else a=m;}}
  el.style.fontSize=a+unit;
}}
document.fonts.ready.then(()=>{{
  document.querySelectorAll('.tp-body').forEach(bx=>fit(bx,bx.querySelector("table"),5.5,11,"pt"));
  document.querySelectorAll('.hp .content').forEach(c=>fit(c,c,8,14,"pt"));
  document.body.dataset.fitted='1';
}});
</script></body></html>"""
(ROOT / f"deck{SUFFIX}.html").write_text(re.sub(r"\(가칭\)\s*", "", doc), encoding="utf-8")
print("pages:", len(pages))

# ---------------------------------------------------------------- 상세판(FULL)
# 노션 특징 문구 전체(data/features_full.md)를 표 다음 장에 「상세 비교 포인트」로 추가한 별도 파일
import os
if os.environ.get("FULL"):
    FEAT = (ROOT / "data" / "features_full.md").read_text(encoding="utf-8")
    FSEC = {}
    for sec in re.split(r"\n(?=## )", FEAT):
        m = re.match(r"## (.+)\n", sec)
        if m:
            FSEC[m.group(1).strip()] = sec[m.end():]

    def feat_html(txt):
        out, depth = [], 0
        def close_to(d):
            nonlocal depth
            while depth > d:
                out.append("</li></ul>"); depth -= 1
        for line in txt.splitlines():
            if not line.strip():
                continue
            mb = re.match(r"\*\*\[(.+?)\]\s*(.*?)\s*\*\*\s*$", line)
            if mb:
                close_to(0)
                if out: out.append("</div>")
                out.append('<div class="fb">')
                sub = f'<span>{cell_html(mb.group(2).lstrip("- "))}</span>' if mb.group(2) else ""
                out.append(f'<h3 class="fb-h">{cell_html(mb.group(1))}{sub}</h3>')
                continue
            ml = re.match(r"( *)- (.*)", line)
            if not ml:
                continue
            d = len(ml.group(1)) // 2 + 1
            if d > depth:
                while depth < d:
                    out.append(f'<ul class="lv{depth+1}"><li>'); depth += 1
            else:
                close_to(d)
                out.append("</li><li>")
            out.append(cell_html(ml.group(2)))
        close_to(0)
        out.append("</div>")
        return "".join(out)

    def detail_page(b):
        key = next(k for k in FSEC if k.startswith(b["table"]))
        return (f'<section class="page dp"><header class="tp-h"><div class="eyebrow"><b>{b["no"]}</b><span>{b["en"]}</span><i>APPENDIX</i></div>'
                f'<h2>{html.escape(b["name"])} <span>상세 비교 포인트</span></h2></header>'
                f'<div class="dp-body"><div class="dp-cols">{feat_html(FSEC[key])}</div></div>{footer()}</section>')

    PAGE_NO[0] = 0
    # 본문(간단판과 동일) → 마무리 → APPENDIX(보틀별 상세 비교 포인트 모음)
    PAGE_NO[0] = 0                               # 1차: APPENDIX 구분 장 번호 계산
    cover(); lineup((1, 1))
    for b in BOTTLES:
        hero_page(b)
        if b["table"]: table_page(b, tbl(b["table"]))
    closing()
    ax_no = PAGE_NO[0] + 1
    PAGE_NO[0] = 0
    pages = [cover(), lineup((ax_no, ax_no + sum(1 for b in BOTTLES if b['table'])))]
    for b in BOTTLES:
        pages.append(hero_page(b))
        if b["table"]:
            pages.append(table_page(b, tbl(b["table"])))
    pages.append(closing())
    det = [b for b in BOTTLES if b["table"]]
    start = PAGE_NO[0] + 2                      # 구분 장 다음 번호부터
    toc = "".join(f'<div class="ax-row"><b>{b["no"]}</b><span>{html.escape(b["name"])}</span><i>{start + i:02d}</i></div>'
                  for i, b in enumerate(det))
    pages.append(f'<section class="page ax"><div class="ax-in"><div class="cv-kicker">APPENDIX</div>'
                 f'<h1>보틀별 <b>상세 비교 포인트</b></h1>'
                 f'<p>본문 비교표의 근거가 되는 특징 문구 전체를 보틀 순서대로 모았습니다.</p>'
                 f'<div class="ax-toc">{toc}</div></div>{footer()}</section>')
    for b in det:
        pages.append(detail_page(b))
    DCSS = """
.dp-body{position:absolute;left:14mm;right:14mm;top:31mm;bottom:17mm}
.dp-cols{column-count:2;column-gap:12mm;column-fill:auto;height:100%;font-size:9pt;line-height:1.6;color:var(--ink2)}
.fb-h{break-after:avoid;font-size:1.02em;font-weight:700;color:var(--ink);padding:.5em 0 .45em;margin-bottom:.5em;border-bottom:0.6pt solid var(--ink);letter-spacing:-0.02em}
.fb{break-inside:avoid-column}\n.fb+.fb{margin-top:1.4em}
.fb-h span{display:block;font-size:.8em;font-weight:500;color:var(--mute);margin-top:.15em}
.dp ul{list-style:none}
.dp ul.lv1>li{position:relative;padding-left:1.1em;margin-bottom:.55em;font-weight:600;color:var(--ink);break-inside:avoid-column}
.dp ul.lv1>li::before{content:"";position:absolute;left:0;top:.62em;width:.38em;height:.38em;background:var(--orange);border-radius:50%}
.dp ul.lv2{margin-top:.25em}
.dp ul.lv2>li{position:relative;padding-left:.95em;margin-bottom:.2em;font-weight:400;color:var(--ink2)}
.dp ul.lv2>li::before{content:"";position:absolute;left:.1em;top:.78em;width:.45em;height:0.5pt;background:var(--mute)}
.dp ul.lv3{margin-top:.15em}
.dp ul.lv3>li{position:relative;padding-left:.9em;font-size:.92em;color:var(--mute)}
.dp ul.lv3>li::before{content:"·";position:absolute;left:.2em}
.dp ul.lv4>li{padding-left:.9em;font-size:.95em;color:var(--mute)}
.dp a{border-bottom:0.5pt solid currentColor}
"""
    FIT = doc[doc.index("<script>"):doc.index("</script>") + 9]
    FIT2 = FIT.replace("document.body.dataset.fitted='1';",
        "document.querySelectorAll('.dp-body').forEach(bx=>{const c=bx.querySelector('.dp-cols');"
        "let a=6,b=12;for(let i=0;i<14;i++){const m=(a+b)/2;c.style.fontSize=m+'pt';"
        "(c.scrollWidth>c.clientWidth+1)?b=m:a=m;}c.style.fontSize=a+'pt';});"
        "document.body.dataset.fitted='1';")
    docf = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>알고케어 뉴트리션 보틀 품질 비교 자료 (상세판)</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>{CSS}{DCSS}</style></head><body>{''.join(pages)}{FIT2}</body></html>"""
    (ROOT / f"deck_full{SUFFIX}.html").write_text(re.sub(r"\(가칭\)\s*", "", docf), encoding="utf-8")
    print("full pages:", len(pages))
