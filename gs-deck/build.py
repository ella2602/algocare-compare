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
}

# 표에서 인쇄물에 맞지 않는 행 라벨 정리
ROW_LABEL = {"판매 링크": "판매처"}

def render_table(rows, dense=False):
    dense=False
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
                label = "제약사 브랜드 인기 · 프리미엄 상품"
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
      name="알고케어 뉴트리션 장용성 초임계 rTG 오메가3", photo="omega",
      hero="글로벌 프리미엄 원료사 프랑스 Polaris,<br>80% 고농도 rTG를 작은 한 알에",
      stats=[("80", "%", "오메가3 농도"), ("377", "mg", "소형 캡슐 1알"), ("3 : 2", "", "EPA : DHA 함량 공개")],
      points=[
        ("프랑스 Polaris 원료", "IFOS 5-Star 인증으로 순도·안전성·품질을 검증받은 프리미엄 오메가3 원료사"),
        ("오메가3 농도 80%", "비교 제품 중 최상위(유한과 동률). 그 외 제품은 60% 또는 농도 미표기"),
        ("rTG · 377mg 소형 캡슐", "1알 EPA+DHA 300mg. 2~3알로 식약처 기능성 용량(500·600·900mg)에 맞춰 섭취"),
        ("장용 캡슐 · 비율 공개", "어취와 더부룩함을 줄인 장용 캡슐, EPA 180 : DHA 120mg 함량 각각 공개"),
      ],
      core="원료사 · 농도 80% · rTG · EPA:DHA 비율 공개 — 네 가지를 모두 갖춘 제품은 비교 제품 중 알고케어뿐"),
 dict(key="probio", no="02", en="PROBIOTICS", table="2. 프로바이오틱스",
      name="알고케어 뉴트리션 프로바이오틱스", photo="probio",
      hero="일동바이오사이언스 유산균,<br>특허 4중 코팅에 장용성 캡슐까지",
      stats=[("500", "억", "투입 균수 (보장 100억)"), ("5", "종", "특허 균주 IDCC"), ("4중+장용", "", "이중 보호 설계")],
      points=[
        ("일동바이오사이언스 특허 균주 5종", "한국인 대상 인체 적용 연구가 있는 IDCC 3201·4301·3302·2201·4101"),
        ("보장균수 100억, 투입 500억", "보장균수의 5배를 투입. 투입 균수까지 공개한 제품은 비교 제품 중 알고케어뿐"),
        ("균체 4중 코팅 + 장용 캡슐", "위산을 지나 장까지 닿도록 이중 보호. 두 기술을 동시에 적용한 제품은 알고케어뿐"),
        ("캡슐 수로 균수 조절", "더 높은 균수가 필요한 고객은 영양 설계 알고리즘에 따라 캡슐 수를 늘려 대응"),
      ],
      core="특허 균주 · 투입 균수 공개 · 균체 코팅과 장용 캡슐 동시 적용"),
 dict(key="mela", no="03", en="MELATONIN", table="3. 멜라토닌",
      name="알고케어 뉴트리션 멜라토닌", photo="mela",
      hero="0.67mg, 국내에 드문 저용량 설계로<br>나에게 맞추는 멜라토닌",
      stats=[("0.67", "mg", "1정 멜라토닌"), ("2", "mg↑", "국내 비교 제품 1회량"), ("단일", "", "멜라토닌 단일 배합")],
      points=[
        ("의도적인 1정 0.67mg 저용량", "사람마다 맞는 용량 편차가 큰 성분이라 개인별 맞춤을 위해 저용량으로 설계"),
        ("국내에서 드문 1mg 이하", "비교한 국내 제품은 모두 1회 2mg 이상 고정. 해외 Pure는 0.5mg 제품을 별도 운영"),
        ("정 수로 찾는 내 용량", "실제 알고케어 섭취자는 0.67~약 5mg 범위에서 정 수를 달리해 각자 맞는 양을 섭취 중"),
        ("멜라토닌 단일 배합", "국내 비교 3종은 모두 복합 배합. 테아닌·마그네슘 등은 알고케어 별도 보틀로 운영"),
      ],
      core="국내 비교군 중 저용량 멜라토닌으로 개인별 맞춤이 가능한 제품은 알고케어뿐"),
 dict(key="sleep", no="03-1", en="SLEEP PRESTIGE", table="3-1.", prerelease=True,
      name="알고케어 프레스티지 수면", photo=None, badge="PRESTIGE",
      hero="멜라토닌 + 테아닌 200mg + Lactium®·Shoden®,<br>하나로 설계한 나이트 보틀",
      stats=[("5", "종", "핵심 성분 배합"), ("200", "mg", "테아닌 (Pure의 4배)"), ("300", "mg", "Lactium®")],
      points=[
        ("하나로 설계한 토탈 나이트 보틀", "멜라토닌 3mg + Lactium® 300mg + GABA 50mg + 테아닌 200mg + Shoden® 120mg"),
        ("Lactium® · Shoden® 배합", "인체 대상 수면 시험 결과가 있는 두 원료를 더함. 국내 비교 제품에는 없는 구성"),
        ("테아닌 200mg", "허브 중심 배합인 Pure Best-Rest(테아닌 50mg)의 4배"),
      ],
      core="국내 비교 제품은 멜라토닌에 테아닌 · 트립토판 · 마그네슘 구성, 알고케어 프레스티지는 Lactium® · Shoden®까지"),
 dict(key="coq", no="04", en="COENZYME Q10", table="4. 코큐텐",
      name="알고케어 뉴트리션 장용성 코큐텐", photo="coq",
      hero="장용성으로 완성한 코큐텐",
      stats=[("장용", "", "연질캡슐 300mg"), ("98", "%", "고순도 · GMO-Free"), ("100~300", "mg", "1일 조절 범위")],
      points=[
        ("장용성 연질캡슐", "위장 편안함을 고려한 설계. 비교 제품 중 장용성 연질캡슐 제형은 알고케어뿐"),
        ("원료사 공개", "Global Merchant 98% GMO-Free 고순도 코큐텐. 국내 비교 제품 중 원료사 공개는 알고케어뿐"),
        ("국내 기능성 원료 유비퀴논", "국내 건강기능식품 기능성은 유비퀴논만 인정 — 항산화 · 높은 혈압 감소에 도움"),
      ],
      core="유비퀴놀을 원하는 고객에게는 알고케어 USA 라인으로 Kaneka 유비퀴놀을 제안"),
 dict(key="coq-usa", no="04-1", en="COENZYME Q10 · USA", table=None, prerelease=True,
      name="(가칭) 알고케어 USA Vascular/Cardio Prime", photo=None, badge="USA",
      hero="Kaneka 유비퀴놀에 Pycnogenol®까지,<br>혈관 케어 프리미엄 보틀",
      stats=[("100", "mg", "Kaneka Ubiquinol®"), ("150", "mg", "Pycnogenol®"), ("4", "종", "활성형 B군")],
      points=[
        ("Kaneka Ubiquinol® 100mg", "미국 프리미엄 시장의 대표 유비퀴놀 원료. Thorne 유비퀴놀과 같은 원료"),
        ("Pycnogenol® 150mg", "Horphag 피크노제놀을 더한 복합 설계"),
        ("활성형 B군", "엽산(Quatrefolic® 5-MTHF) · B6(P5P) · B2(R5P) · B12(메틸코발라민)"),
        ("미국용 · 국내 직구 고객용", "유비퀴놀 형태를 선호하는 해외 직구 고객층의 니즈를 반영한 설계"),
      ],
      core="미국 출시 예정 · 원료사 Kaneka · Horphag · Quatrefolic"),
 dict(key="lutein", no="05", en="LUTEIN & ZEAXANTHIN", table="5. 루테인",
      name="알고케어 뉴트리션 장용성 루테인지아잔틴", photo="lutein",
      hero="매일 챙기는 눈 건강 기본 루틴",
      stats=[("10+2", "mg", "루테인 + 지아잔틴"), ("2", "캡슐", "최대 20+4mg까지"), ("장용", "", "연질캡슐 300mg")],
      points=[
        ("루테인 10 + 지아잔틴 2mg 단일 배합", "부담 없이 시작할 수 있는 눈 영양제 포지션"),
        ("Lute-gen 원료", "원료사 Lute-gen(Bio-gen Extracts)의 개별인정형 원료 사용"),
        ("최대 2캡슐까지 조절", "필요에 따라 루테인 20mg · 지아잔틴 4mg까지"),
        ("장용 연질캡슐", "비교 제품 중 유일한 장용 연질캡슐로 위 부담을 덜음"),
      ],
      core="눈 피로 관리까지 원하는 고객에게는 프레스티지 라인을 제안"),
 dict(key="lutein-pre", no="05-1", en="EYE PRESTIGE", table=None, prerelease=True,
      name="알고케어 프레스티지 루테인지아잔틴", photo=None, badge="PRESTIGE",
      hero="Indena Mirtoselect® 빌베리와<br>아스타잔틴을 더한 프리미엄 눈 건강",
      stats=[("160", "mg", "Mirtoselect® 빌베리"), ("6", "mg", "아스타잔틴"), ("3", "가지", "기능성 함량 성분")],
      points=[
        ("황반 관리 + 눈 피로 관리", "루테인지아잔틴에 아스타잔틴 · 빌베리를 한 보틀에 담은 프레스티지 눈 케어 라인"),
        ("Indena Mirtoselect® 빌베리 160mg", "세계적인 식물 추출물 원료사 Indena(이탈리아). 개별인정형 기능성 함량으로 배합"),
        ("3가지 모두 기능성 함량", "루테인 · 아스타잔틴 · 빌베리를 모두 기능성 함량으로 담은 제품은 비교 제품 중 알고케어뿐"),
      ],
      core="일동 마이니 · 고려은단은 루테인지아잔틴 + 아스타잔틴 2가지 배합"),
 dict(key="mag", no="06", en="MAGNESIUM", table="6. 마그네슘",
      name="알고케어 시너지 마그네슘", photo="mag",
      hero="아쿠아민·젖산·글루콘산,<br>3종 마그네슘을 한 보틀에",
      stats=[("3", "종", "마그네슘 원료 복합"), ("3", "곳", "원료사 모두 공개"), ("180~385", "mg", "1일 조절 범위")],
      points=[
        ("마그네슘 3종 복합 설계", "Aquamin(해조) + 젖산(유기산) + 글루콘산(유기산). 비교 제품은 원료 1종만 사용"),
        ("원료사 3곳 공개", "Superior Powders(영국) · NOVICHEM(폴란드) · Novotech(미국)"),
        ("1정 25.71mg 단위 조절", "180~385mg까지 조절. 국내 비교 제품은 1회 섭취량 고정(175~315mg)"),
      ],
      core="유기산 비중을 높인 프레스티지, 킬레이트 마그네슘 USA 라인까지"),
 dict(key="mag-line", no="06-1", en="MAGNESIUM · PRESTIGE & USA", table=None, prerelease=True,
      name="알고케어 프레스티지 마그네슘 · (가칭) 알고케어 USA Magnesium", photo=None, badge="PRESTIGE · USA",
      split=[
        dict(label="PRESTIGE", sub="알고케어 프레스티지 마그네슘 · 국내 출시 예정",
             hero="유기산 마그네슘 비중을 크게 높인 프레스티지",
             points=[
               ("유기산 마그네슘 50%", "흡수율이 좋은 것으로 알려진 유기산 마그네슘 비중을 50%로 (Mg 원소 기준)"),
               ("리포좀(메타좀) 마그네슘", "베이직 라인의 아쿠아민 대신 리포좀(메타좀) 마그네슘 사용"),
               ("유기산 비율 15% → 78%", "마그네슘 원료 중 유기산 마그네슘 비율, 베이직 대비 (원료 중량 기준)"),
             ]),
        dict(label="USA", sub="(가칭) 알고케어 USA Magnesium · 미국 출시 예정",
             hero="글로벌 킬레이트 원료사 Albion TRAACS® 비스글리시네이트, 킬레이트 마그네슘 200mg",
             points=[
               ("Albion TRAACS®", "세계적인 킬레이트 미네랄 원료사 Albion의 Magnesium Bisglycinate Chelate"),
               ("비스글리시네이트 단일 배합", "다른 형태를 섞지 않은 단일 배합 — 미국 프리미엄 마그네슘의 표준"),
               ("직구 고객 니즈 반영", "국내 규정상 킬레이트 마그네슘은 원료로 사용 불가. 해외 직구 수요에 대응"),
             ]),
      ]),
 dict(key="milk", no="07", en="MILK THISTLE", table="7. 밀크씨슬",
      name="알고케어 뉴트리션 밀크씨슬", photo="milk",
      hero="글로벌 프리미엄 허브 원료사<br>Indena의 밀크씨슬",
      stats=[("Indena", "", "이탈리아 원료사"), ("60", "%", "실리마린 순도"), ("43.33", "mg", "1정 실리마린")],
      points=[
        ("Indena(이탈리아) 원료", "세계적인 허브 추출물 원료사의 순도 60% 밀크씨슬. 국내 비교 제품은 원료사 확인 불가"),
        ("실리마린 130mg", "식약처 기능성 함량에 맞춘 설계"),
        ("1정 43.33mg 단위 맞춤", "개인별 미량 맞춤 가능. 비교 제품은 1알 130mg으로 1회 복용량 고정"),
      ],
      core="원료사를 밝힌 밀크씨슬은 비교 제품 중 알고케어뿐"),
 dict(key="banaba", no="08", en="BANABA", table="8. 바나바",
      name="알고케어 뉴트리션 바나바", photo="banaba",
      hero="혈당 건강이 필요할 때,<br>겹치지 않게 더하는 바나바",
      stats=[("1.3", "mg", "코로솔산"), ("30", "μg", "크롬 최소 배합"), ("STAR HI", "", "원료사 공개")],
      points=[
        ("필요한 사람에게만 더하는 보틀", "알고케어 사용자 중 혈당 관리가 필요한 사람에게 맞춤으로 더함"),
        ("코로솔산 1.3mg + 크롬 30μg", "식약처 기능성 함량만 담은 최소 배합. 비타민 · 미네랄은 멀티와 중복 섭취 방지"),
        ("원료사 STAR HI 공개", "비교 제품 4종은 모두 원료사 미표기"),
      ],
      core="알고케어 시스템 안에서 중복 없이 맞춤으로 더하는 보틀"),
 dict(key="rhod", no="09", en="RHODIOLA & THEANINE", table="9. 홍경천",
      name="알고케어 뉴트리션 홍경천&테아닌", photo="rhod",
      hero="스트레스 관리에 집중한<br>홍경천·테아닌 보틀",
      stats=[("200", "mg", "홍경천 추출물"), ("200", "mg", "L-테아닌"), ("4.2", "mg", "로사빈")],
      points=[
        ("홍경천 + 테아닌 한 보틀", "비교 제품 중 둘을 함께 담은 제품은 모어네이처와 알고케어 2종뿐"),
        ("원료사 공개", "홍경천 Nektium(스페인) · 테아닌 Molecules bio labs(인도). 비교 제품 4종은 모두 미표기"),
        ("두 성분 외 배합 없음", "마그네슘 · 비타민B군 · 아연은 알고케어 별도 보틀로 제공해 중복 섭취 방지"),
      ],
      core="여에스더 · 동아 · 종근당은 홍경천 없는 테아닌 중심 제품"),
]

LOGO_BLACK = (ROOT / "assets" / "algocare.svg").read_text().replace("#FAF9F9", "#0A0909")
LOGO_WHITE = (ROOT / "assets" / "algocare.svg").read_text()

def logo(dark=False, h=14):
    svg = LOGO_WHITE if dark else LOGO_BLACK
    return svg.replace('width="98" height="22"', f'height="{h}" width="{h*98/22:.1f}"', 1)

PAGE_NO = [0]

def footer(dark=False, src=True):
    PAGE_NO[0] += 1
    note = "자료 기준 2026.11.03 · 각 사 공식몰 · GS SHOP · 제품 라벨 표기 기준 · 월 환산가는 조사 시점 판매가 기준으로 변동 가능" if src else ""
    return (f'<footer class="ft"><span class="ft-logo">{logo(dark, 11)}</span>'
            f'<span class="ft-note">{note}</span><span class="ft-no">{PAGE_NO[0]:02d}</span></footer>')

def stats_html(stats):
    return '<div class="stats">' + "".join(
        f'<div class="stat"><div class="sv">{html.escape(v)}<small>{html.escape(u)}</small></div>'
        f'<div class="sl">{html.escape(l)}</div></div>' for v, u, l in stats) + "</div>"

def points_html(points, cols=2):
    return f'<div class="points cols{cols}">' + "".join(
        f'<div class="pt"><div class="pt-n">{i:02d}</div><div><h4>{html.escape(t)}</h4><p>{html.escape(d)}</p></div></div>'
        for i, (t, d) in enumerate(points, 1)) + "</div>"

def hero_page(b):
    pre = b.get("prerelease")
    if b.get("photo"):
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
                   f'<div class="pname">{html.escape(b["name"])}</div>'
                   f'<h1 class="hero">{b["hero"]}</h1>'
                   f'{stats_html(b["stats"])}'
                   f'{points_html(b["points"])}'
                   f'<div class="core-wrap"><div class="core"><span>KEY</span>{html.escape(b["core"])}</div></div>')
    return f'<section class="page hp">{visual}<div class="content">{content}</div>{footer()}</section>'

def table_page(b, rows, title_extra=""):
    ncols = len(rows[0])
    dense = ncols >= 7
    return (f'<section class="page tp"><header class="tp-h"><div class="eyebrow"><b>{b["no"]}</b><span>{b["en"]}</span><i>COMPARISON</i></div>'
            f'<h2>{html.escape(b["name"])}{title_extra} <span>vs 비교 제품</span></h2></header>'
            f'<div class="tp-body">{render_table(rows, dense)}</div>'
            f'<div class="legend"><span class="lg algo"></span>알고케어 '
            + ('<span class="lg algo-pre"></span>알고케어 출시 예정 ' if any("출시 예정" in g for g in rows[0]) else '') +
            f'<span class="lg gs"></span>GS SHOP 매칭 상품 <span class="lg pharma"></span>제약사 브랜드 인기 · 프리미엄 상품'
            f'<span class="lg-note">「-」 미표기 · 미확인 / 「없음」 해당 성분 없음</span></div>{footer()}</section>')

def cover():
    imgs = "".join(f'<div class="cv-b" style="background-image:url(img/{k}_bottle.jpg)"></div>'
                   for k in ["omega", "probio", "mela", "coq", "lutein", "mag", "milk", "banaba", "rhod"])
    return (f'<section class="page cover"><div class="cv-top">{logo(True, 20)}<span>GS SHOP MD TEAM · 2026.11</span></div>'
            f'<div class="cv-main"><div class="cv-kicker">ALGOCARE NUTRITION BOTTLE</div>'
            f'<h1>알고케어 뉴트리션 보틀<br><b>품질 비교 자료</b></h1>'
            f'<p>원료사 · 함량 · 제형 · 가격까지, 9종 보틀과 출시 예정 라인을<br>GS SHOP 매칭 상품 · 제약사 브랜드 · 해외 프리미엄 제품과 나란히 비교했습니다.</p></div>'
            f'<div class="cv-row">{imgs}</div></section>')

def lineup():
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
    return (f'<section class="page lineup"><header class="tp-h"><div class="eyebrow"><b>00</b><span>LINE-UP</span><i>HERO LINES</i></div>'
            f'<h2>한눈에 보는 알고케어 뉴트리션 라인업</h2></header><div class="lu-grid">{items}</div>{footer()}</section>')

def closing():
    pillars = [
        ("SOURCE", "원료사를 밝힙니다", "Polaris · Indena · Kaneka · Albion · 일동바이오사이언스 — 비교 제품 다수가 미표기인 원료사를 공개"),
        ("DOSE", "알 수로 맞춥니다", "오메가3 · 멜라토닌 · 마그네슘 · 밀크씨슬까지, 고정 1회분이 아닌 정 · 캡슐 단위 조절"),
        ("SYSTEM", "겹치지 않게 설계합니다", "단일 배합 보틀로 멀티비타민미네랄과의 중복 섭취를 막는 알고케어 시스템"),
    ]
    cards = "".join(f'<div class="pl"><div class="pl-en">{e}</div><h3>{t}</h3><p>{html.escape(d)}</p></div>' for e, t, d in pillars)
    return (f'<section class="page closing"><div class="cl-in"><div class="cv-kicker">WHY ALGOCARE</div>'
            f'<h1>같은 이름의 영양제라도,<br><b>설계는 다릅니다.</b></h1><div class="pillars">{cards}</div></div>'
            f'<div class="cl-logo">{logo(True, 22)}</div></section>')

CSS = (ROOT / "deck.css").read_text(encoding="utf-8")

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
(ROOT / "deck.html").write_text(doc, encoding="utf-8")
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
        return (f'<section class="page dp"><header class="tp-h"><div class="eyebrow"><b>{b["no"]}</b><span>{b["en"]}</span><i>DETAIL</i></div>'
                f'<h2>{html.escape(b["name"])} <span>상세 비교 포인트</span></h2></header>'
                f'<div class="dp-body"><div class="dp-cols">{feat_html(FSEC[key])}</div></div>{footer()}</section>')

    PAGE_NO[0] = 0
    pages = [cover(), lineup()]
    for b in BOTTLES:
        pages.append(hero_page(b))
        if b["table"]:
            pages.append(table_page(b, tbl(b["table"])))
            pages.append(detail_page(b))
    pages.append(closing())
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
    (ROOT / "deck_full.html").write_text(docf, encoding="utf-8")
    print("full pages:", len(pages))
