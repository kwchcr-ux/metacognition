#!/usr/bin/env python3
"""
vedic_chart.py - 조티샤 차트 생성기
Swiss Ephemeris 기반, 라히리 아야남샤 적용 항성 황도 계산.

사용법:
    python3 vedic_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --place "창원" --gender M
    python3 vedic_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --lat 35.228 --lon 128.681 --gender F
    python3 vedic_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --place "서울" --gender M --markdown

의존 패키지:
    pip3 install pyswisseph
"""

import sys
import os
import argparse
import math
from datetime import datetime, timedelta

try:
    import swisseph as swe
except ImportError:
    print("오류: pyswisseph 패키지가 필요합니다.")
    print("설치: pip3 install pyswisseph")
    sys.exit(1)

# ─── 상수 ───

RASHIS = [
    ("Aries", "메샤(양)"),
    ("Taurus", "브리샤바(황소)"),
    ("Gemini", "미투나(쌍둥이)"),
    ("Cancer", "카르카(게)"),
    ("Leo", "심하(사자)"),
    ("Virgo", "칸야(처녀)"),
    ("Libra", "툴라(천칭)"),
    ("Scorpio", "브리쉬치카(전갈)"),
    ("Sagittarius", "다누(사수)"),
    ("Capricorn", "마카라(염소)"),
    ("Aquarius", "쿰바(물병)"),
    ("Pisces", "미나(물고기)"),
]

# 조티샤 7행성 + 라후/케투
PLANETS = [
    (swe.SUN, "Sun", "수리아(태양)"),
    (swe.MOON, "Moon", "찬드라(달)"),
    (swe.MARS, "Mars", "망갈(화성)"),
    (swe.MERCURY, "Mercury", "부다(수성)"),
    (swe.JUPITER, "Jupiter", "구루(목성)"),
    (swe.VENUS, "Venus", "슈크라(금성)"),
    (swe.SATURN, "Saturn", "샤니(토성)"),
    (swe.MEAN_NODE, "Rahu", "라후(북교점)"),
]

# 27 낙샤트라 (각 13°20' = 800')
NAKSHATRAS = [
    ("Ashwini", "아쉬위니", "케투"),
    ("Bharani", "바라니", "금성"),
    ("Krittika", "크리티카", "태양"),
    ("Rohini", "로히니", "달"),
    ("Mrigashira", "므리가시라", "화성"),
    ("Ardra", "아르드라", "라후"),
    ("Punarvasu", "푸나르바수", "목성"),
    ("Pushya", "푸쉬야", "토성"),
    ("Ashlesha", "아쉴레샤", "수성"),
    ("Magha", "마가", "케투"),
    ("Purva Phalguni", "푸르바 팔구니", "금성"),
    ("Uttara Phalguni", "우타라 팔구니", "태양"),
    ("Hasta", "하스타", "달"),
    ("Chitra", "치트라", "화성"),
    ("Swati", "스와티", "라후"),
    ("Vishakha", "비샤카", "목성"),
    ("Anuradha", "아누라다", "토성"),
    ("Jyeshtha", "지에쉬타", "수성"),
    ("Mula", "물라", "케투"),
    ("Purva Ashadha", "푸르바 아샤다", "금성"),
    ("Uttara Ashadha", "우타라 아샤다", "태양"),
    ("Shravana", "쉬라바나", "달"),
    ("Dhanishta", "다니쉬타", "화성"),
    ("Shatabhisha", "샤타비샤", "라후"),
    ("Purva Bhadrapada", "푸르바 바드라파다", "목성"),
    ("Uttara Bhadrapada", "우타라 바드라파다", "토성"),
    ("Revati", "레바티", "수성"),
]

# 비무샤뜨리 다샤 행성 순서와 기간(년)
DASHA_SEQUENCE = [
    ("케투", 7),
    ("금성", 20),
    ("태양", 6),
    ("달", 10),
    ("화성", 7),
    ("라후", 18),
    ("목성", 16),
    ("토성", 19),
    ("수성", 17),
]
DASHA_TOTAL = 120  # 총 120년

# 낙샤트라 → 다샤 시작 행성 매핑 (낙샤트라 지배성 기준)
NAKSHATRA_DASHA_LORD = {
    "케투": 0, "금성": 1, "태양": 2, "달": 3, "화성": 4,
    "라후": 5, "목성": 6, "토성": 7, "수성": 8,
}

# 행성 존엄성 (Own / Exaltation / Debilitation)
# 라시 인덱스: 0=Aries ... 11=Pisces
OWNERSHIP = {
    "Sun": [4],            # Leo
    "Moon": [3],           # Cancer
    "Mars": [0, 7],        # Aries, Scorpio
    "Mercury": [2, 5],     # Gemini, Virgo
    "Jupiter": [8, 11],    # Sagittarius, Pisces
    "Venus": [1, 6],       # Taurus, Libra
    "Saturn": [9, 10],     # Capricorn, Aquarius
    "Rahu": [10],          # Aquarius (일부 해석)
    "Ketu": [7],           # Scorpio (일부 해석)
}

EXALTATION = {
    "Sun": (0, 10),     # Aries 10°
    "Moon": (1, 3),     # Taurus 3°
    "Mars": (9, 28),    # Capricorn 28°
    "Mercury": (5, 15), # Virgo 15°
    "Jupiter": (3, 5),  # Cancer 5°
    "Venus": (11, 27),  # Pisces 27°
    "Saturn": (6, 20),  # Libra 20°
    "Rahu": (1, 20),    # Taurus 20°
    "Ketu": (7, 20),    # Scorpio 20°
}

DEBILITATION = {
    "Sun": (6,),     # Libra
    "Moon": (7,),    # Scorpio
    "Mars": (3,),    # Cancer
    "Mercury": (11,),# Pisces
    "Jupiter": (9,), # Capricorn
    "Venus": (5,),   # Virgo
    "Saturn": (0,),  # Aries
    "Rahu": (7,),    # Scorpio
    "Ketu": (1,),    # Taurus
}

# 바바(Bhava) = 하우스 의미
BHAVA_MEANINGS = {
    1: "탄누(자아/신체)",
    2: "다나(재물/가족)",
    3: "사하자(형제/용기)",
    4: "수카(가정/마음의 평화)",
    5: "푸트라(자녀/창의성/지성)",
    6: "아리(적/질병/봉사)",
    7: "칼라트라(배우자/파트너십)",
    8: "아유(수명/변환/비밀)",
    9: "다르마(행운/스승/철학)",
    10: "카르마(직업/사회적 지위)",
    11: "라바(이득/소망 성취)",
    12: "비야야(손실/해탈/해외)",
}

# 한국 주요 도시 좌표
CITY_COORDS = {
    "서울": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756),
    "대구": (35.8714, 128.6014),
    "인천": (37.4563, 126.7052),
    "광주": (35.1595, 126.8526),
    "대전": (36.3504, 127.3845),
    "울산": (35.5384, 129.3114),
    "수원": (37.2636, 127.0286),
    "창원": (35.2280, 128.6811),
    "성남": (37.4200, 127.1265),
    "고양": (37.6564, 126.8350),
    "용인": (37.2411, 127.1776),
    "청주": (36.6424, 127.4890),
    "전주": (35.8242, 127.1480),
    "천안": (36.8151, 127.1139),
    "포항": (36.0190, 129.3435),
    "제주": (33.4996, 126.5312),
    "김해": (35.2285, 128.8894),
    "진주": (35.1801, 128.1076),
    "원주": (37.3422, 127.9202),
    "춘천": (37.8813, 127.7300),
    "안산": (37.3219, 126.8309),
    "안양": (37.3943, 126.9568),
    "평택": (36.9908, 127.0859),
    "익산": (35.9483, 126.9577),
    "목포": (34.8118, 126.3922),
    "여수": (34.7604, 127.6622),
    "순천": (34.9506, 127.4872),
    "군산": (35.9676, 126.7370),
    "경주": (35.8562, 129.2247),
    "거제": (34.8806, 128.6211),
    "통영": (34.8544, 128.4332),
    "양산": (35.3350, 129.0373),
    "구미": (36.1195, 128.3446),
    "김천": (36.1398, 128.1136),
    "안동": (36.5684, 128.7294),
    "강릉": (37.7519, 128.8761),
    "속초": (38.2070, 128.5918),
    "동해": (37.5244, 129.1143),
    "삼척": (37.4500, 129.1650),
    "태백": (37.1641, 128.9856),
    "영주": (36.8058, 128.6240),
    "문경": (36.5866, 128.1991),
    "상주": (36.4109, 128.1590),
    "영천": (35.9733, 128.9385),
    "밀양": (35.5038, 128.7465),
    "사천": (35.0034, 128.0647),
    "남원": (35.4164, 127.3905),
    "정읍": (35.5699, 126.8568),
    "김제": (35.8037, 126.8808),
    "나주": (34.9909, 126.7115),
    "광양": (34.9407, 127.6958),
    "서산": (36.7849, 126.4503),
    "당진": (36.8895, 126.6297),
    "아산": (36.7898, 127.0018),
    "논산": (36.1871, 127.0987),
    "보령": (36.3334, 126.6127),
    "공주": (36.4465, 127.1190),
    "세종": (36.4800, 127.2590),
}

# 영문 → 한글 도시명 매핑
CITY_NAME_EN = {
    "seoul": "서울", "busan": "부산", "daegu": "대구", "incheon": "인천",
    "gwangju": "광주", "daejeon": "대전", "ulsan": "울산", "suwon": "수원",
    "changwon": "창원", "seongnam": "성남", "goyang": "고양", "yongin": "용인",
    "cheongju": "청주", "jeonju": "전주", "cheonan": "천안", "pohang": "포항",
    "jeju": "제주", "gimhae": "김해", "jinju": "진주", "wonju": "원주",
    "chuncheon": "춘천", "ansan": "안산", "anyang": "안양", "pyeongtaek": "평택",
    "iksan": "익산", "mokpo": "목포", "yeosu": "여수", "suncheon": "순천",
    "gunsan": "군산", "gyeongju": "경주", "geoje": "거제", "tongyeong": "통영",
    "yangsan": "양산", "gumi": "구미", "gimcheon": "김천", "andong": "안동",
    "gangneung": "강릉", "sokcho": "속초", "donghae": "동해", "samcheok": "삼척",
    "taebaek": "태백", "yeongju": "영주", "mungyeong": "문경", "sangju": "상주",
    "yeongcheon": "영천", "miryang": "밀양", "sacheon": "사천", "namwon": "남원",
    "jeongeup": "정읍", "gimje": "김제", "naju": "나주", "gwangyang": "광양",
    "seosan": "서산", "dangjin": "당진", "asan": "아산", "nonsan": "논산",
    "boryeong": "보령", "gongju": "공주", "sejong": "세종",
}


# ─── 유틸리티 ───

def get_ayanamsa(jd):
    """라히리 아야남샤 반환"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.get_ayanamsa_ut(jd)


def tropical_to_sidereal(tropical_lon, ayanamsa):
    """회귀 황도 → 항성 황도 변환"""
    sid = (tropical_lon - ayanamsa) % 360
    return sid


def deg_to_rashi(longitude):
    """항성 경도(0~360) → (라시 인덱스, 도, 분)"""
    rashi_idx = int(longitude / 30) % 12
    deg_in_rashi = longitude - rashi_idx * 30
    degrees = int(deg_in_rashi)
    minutes = int((deg_in_rashi - degrees) * 60)
    return rashi_idx, degrees, minutes


def format_rashi_pos(longitude):
    """항성 경도 → '라시 도°분'' 문자열"""
    rashi_idx, deg, min_ = deg_to_rashi(longitude)
    en, kr = RASHIS[rashi_idx]
    return f"{en} ({kr}) {deg}°{min_:02d}'"


def get_nakshatra(longitude):
    """항성 경도 → (낙샤트라 인덱스, 파다(1~4), 낙샤트라 내 도수)"""
    nak_size = 360.0 / 27  # 13°20' = 13.3333...°
    nak_idx = int(longitude / nak_size) % 27
    pos_in_nak = longitude - nak_idx * nak_size
    pada = int(pos_in_nak / (nak_size / 4)) + 1
    if pada > 4:
        pada = 4
    return nak_idx, pada, pos_in_nak


def get_navamsha_rashi(longitude):
    """항성 경도 → 나바암샤(D-9) 라시 인덱스
    각 라시를 9등분 (3°20'씩), 불의 라시(0,4,8)는 양자리부터,
    흙의 라시(1,5,9)는 염소자리부터, 바람의 라시(2,6,10)는 천칭부터,
    물의 라시(3,7,11)는 게자리부터 시작"""
    rashi_idx = int(longitude / 30) % 12
    deg_in_rashi = longitude - rashi_idx * 30
    navamsha_part = int(deg_in_rashi / (30.0 / 9))
    if navamsha_part > 8:
        navamsha_part = 8

    # 원소별 시작점
    element_starts = {
        0: 0,   # Fire (Aries, Leo, Sag) → starts from Aries
        1: 9,   # Earth (Taurus, Virgo, Cap) → starts from Capricorn
        2: 6,   # Air (Gemini, Libra, Aquarius) → starts from Libra
        3: 3,   # Water (Cancer, Scorpio, Pisces) → starts from Cancer
    }

    element_order = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
    element = element_order[rashi_idx]
    start = element_starts[element]
    navamsha_rashi = (start + navamsha_part) % 12
    return navamsha_rashi


def get_dignity(planet_name, rashi_idx):
    """행성의 존엄성 판단"""
    # 라후/케투 이름 매핑
    name = planet_name
    if name == "Rahu":
        name = "Rahu"
    elif name == "Ketu":
        name = "Ketu"

    # 자기 궁
    if name in OWNERSHIP and rashi_idx in OWNERSHIP[name]:
        return "자기궁(Own)"

    # 고양
    if name in EXALTATION and rashi_idx == EXALTATION[name][0]:
        return "고양(Exalted)"

    # 쇠약
    if name in DEBILITATION and rashi_idx == DEBILITATION[name][0]:
        return "쇠약(Debilitated)"

    return ""


# ─── 비무샤뜨리 다샤 계산 ───

def calculate_dasha(moon_longitude, birth_jd):
    """달의 낙샤트라 위치로 비무샤뜨리 마하다샤 계산"""
    nak_idx, pada, pos_in_nak = get_nakshatra(moon_longitude)
    nak_en, nak_kr, nak_lord = NAKSHATRAS[nak_idx]

    # 출생 시점 낙샤트라 진행률 → 첫 다샤의 남은 기간 계산
    nak_size = 360.0 / 27
    fraction_elapsed = pos_in_nak / nak_size  # 낙샤트라 내에서 이미 지나간 비율

    # 다샤 시작 행성 인덱스
    dasha_start_idx = NAKSHATRA_DASHA_LORD[nak_lord]

    # 첫 다샤의 남은 기간
    first_dasha_name, first_dasha_years = DASHA_SEQUENCE[dasha_start_idx]
    remaining_years = first_dasha_years * (1 - fraction_elapsed)

    # 출생일 기준 다샤 테이블 생성
    dashas = []
    # JD를 datetime으로 변환
    birth_date = jd_to_datetime(birth_jd)
    current_date = birth_date

    # 첫 다샤 (남은 기간)
    end_date = current_date + timedelta(days=remaining_years * 365.25)
    dashas.append({
        "lord": first_dasha_name,
        "years": first_dasha_years,
        "remaining": remaining_years,
        "start": current_date,
        "end": end_date,
        "is_first": True,
    })
    current_date = end_date

    # 이후 다샤
    for cycle in range(2):  # 2사이클이면 충분
        for i in range(9):
            idx = (dasha_start_idx + 1 + i) % 9
            if cycle == 0 and i == 0:
                # 첫 사이클의 두 번째 다샤부터
                pass
            dasha_name, dasha_years = DASHA_SEQUENCE[idx]
            end_date = current_date + timedelta(days=dasha_years * 365.25)
            dashas.append({
                "lord": dasha_name,
                "years": dasha_years,
                "remaining": dasha_years,
                "start": current_date,
                "end": end_date,
                "is_first": False,
            })
            current_date = end_date
            if current_date > birth_date + timedelta(days=120 * 365.25):
                break
        if current_date > birth_date + timedelta(days=120 * 365.25):
            break

    return dashas, nak_idx


def jd_to_datetime(jd):
    """율리우스일 → datetime"""
    result = swe.revjul(jd)
    year, month, day, hour_float = result
    hours = int(hour_float)
    minutes = int((hour_float - hours) * 60)
    # KST = UTC + 9
    try:
        dt = datetime(year, month, day, hours, minutes) + timedelta(hours=9)
    except ValueError:
        dt = datetime(year, month, day, 0, 0) + timedelta(hours=9)
    return dt


# ─── 요가 계산 ───

def detect_yogas(planet_data, lagna_rashi):
    """주요 요가(행성 조합) 검출"""
    yogas = []

    # 행성 이름 → 라시 인덱스 매핑
    planet_rashis = {}
    for p in planet_data:
        planet_rashis[p["name_en"]] = p["rashi_idx"]

    # 행성 이름 → 경도 매핑
    planet_lons = {}
    for p in planet_data:
        planet_lons[p["name_en"]] = p["sid_longitude"]

    # 켄드라 (1, 4, 7, 10 하우스에 해당하는 라시)
    kendras = [(lagna_rashi + offset) % 12 for offset in [0, 3, 6, 9]]
    # 트리코나 (1, 5, 9 하우스)
    trikonas = [(lagna_rashi + offset) % 12 for offset in [0, 4, 8]]

    # 1. 가자케사리 요가: 목성과 달이 서로 켄드라에 있을 때
    if "Jupiter" in planet_rashis and "Moon" in planet_rashis:
        jup_r = planet_rashis["Jupiter"]
        moon_r = planet_rashis["Moon"]
        diff = (jup_r - moon_r) % 12
        if diff in [0, 3, 6, 9]:
            yogas.append({
                "name": "가자케사리 요가 (Gajakesari Yoga)",
                "desc": "목성과 달이 서로 켄드라 관계 — 지혜와 명성의 잠재력이 있으나, 그것을 '타고난 것'으로 착각하면 노력을 멈춘다",
                "planets": "목성 + 달",
            })

    # 2. 부다디트야 요가: 태양과 수성이 같은 하우스
    if "Sun" in planet_rashis and "Mercury" in planet_rashis:
        if planet_rashis["Sun"] == planet_rashis["Mercury"]:
            yogas.append({
                "name": "부다디트야 요가 (Budhaditya Yoga)",
                "desc": "태양과 수성이 합궁 — 지적 능력과 표현력의 조합이지만, 연소(combust) 여부에 따라 '머리는 좋은데 판단이 흐린' 구조가 될 수 있다",
                "planets": "태양 + 수성",
            })

    # 3. 판차마하푸루샤 요가: 화성/수성/목성/금성/토성이 자기궁 또는 고양궁에서 켄드라에 위치
    mahapurusha_planets = {
        "Mars": "루치카 요가 (Ruchaka)",
        "Mercury": "바드라 요가 (Bhadra)",
        "Jupiter": "함사 요가 (Hamsa)",
        "Venus": "말라비아 요가 (Malavya)",
        "Saturn": "샤샤 요가 (Sasha)",
    }
    for pname, yoga_name in mahapurusha_planets.items():
        if pname in planet_rashis:
            r = planet_rashis[pname]
            dignity = get_dignity(pname, r)
            if ("Own" in dignity or "Exalted" in dignity) and r in kendras:
                desc_map = {
                    "Mars": "행동력과 용기의 구조 — 그러나 이것이 '나는 강한 사람'이라는 자기 서사를 만들어 유연성을 잃게 한다",
                    "Mercury": "지적 명석함의 구조 — 그러나 '나는 합리적'이라는 확신이 감정적 맹점을 은폐한다",
                    "Jupiter": "지혜와 도덕성의 구조 — 그러나 '나는 선한 사람'이라는 서사가 자기 욕망을 직시하지 못하게 한다",
                    "Venus": "감각적 풍요의 구조 — 그러나 '나는 아름다운 것을 안다'는 믿음이 집착을 미화한다",
                    "Saturn": "인내와 규율의 구조 — 그러나 '나는 책임감 있다'는 서사가 통제욕을 은폐한다",
                }
                yogas.append({
                    "name": f"판차마하푸루샤: {yoga_name}",
                    "desc": desc_map.get(pname, ""),
                    "planets": pname,
                })

    # 4. 칼사르파 요가: 모든 행성이 라후-케투 축 한쪽에 있을 때
    if "Rahu" in planet_lons:
        rahu_lon = planet_lons["Rahu"]
        ketu_lon = (rahu_lon + 180) % 360
        # 라후→케투 방향(시계)으로 모든 행성이 있는지 확인
        all_one_side = True
        all_other_side = True
        for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            if pname not in planet_lons:
                continue
            plon = planet_lons[pname]
            # 라후에서 케투까지의 호(시계 방향)
            if rahu_lon < ketu_lon:
                in_arc = rahu_lon <= plon <= ketu_lon
            else:
                in_arc = plon >= rahu_lon or plon <= ketu_lon
            if not in_arc:
                all_one_side = False
            else:
                all_other_side = False

        if all_one_side or all_other_side:
            yogas.append({
                "name": "칼사르파 요가 (Kala Sarpa Yoga)",
                "desc": "모든 행성이 라후-케투 축 한쪽에 몰림 — 삶의 특정 영역에 에너지가 극단적으로 집중되며, 나머지를 '내 영역이 아니다'라고 체념하는 구조",
                "planets": "전 행성 + 라후/케투 축",
            })

    # 5. 켐드루마 요가: 달 양옆 하우스(2nd/12th from Moon)에 행성이 없을 때
    if "Moon" in planet_rashis:
        moon_r = planet_rashis["Moon"]
        adjacent = [(moon_r + 1) % 12, (moon_r - 1) % 12]
        has_adjacent = False
        for pname in ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            if pname in planet_rashis and planet_rashis[pname] in adjacent:
                has_adjacent = True
                break
        if not has_adjacent:
            yogas.append({
                "name": "켐드루마 요가 (Kemadruma Yoga)",
                "desc": "달 양옆에 행성이 없음 — 정서적 고립감의 구조. '혼자서도 괜찮다'는 서사가 실은 '도움을 요청하는 법을 모른다'의 포장일 수 있다",
                "planets": "달 (고립)",
            })

    return yogas


# ─── 메인 계산 ───

def calculate_chart(year, month, day, hour, minute, lat, geo_lon, gender="M"):
    """조티샤 차트 전체 계산"""
    ephe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ephe")
    swe.set_ephe_path(ephe_path)

    # UTC 변환 (KST = UTC+9)
    utc_hour = hour - 9 + minute / 60.0
    utc_day = day
    utc_month = month
    utc_year = year
    if utc_hour < 0:
        utc_hour += 24
        utc_day -= 1
    elif utc_hour >= 24:
        utc_hour -= 24
        utc_day += 1

    jd = swe.julday(utc_year, utc_month, utc_day, utc_hour)

    # 아야남샤
    ayanamsa = get_ayanamsa(jd)

    # 라그나 (상승궁) 계산 — Placidus로 ASC를 구한 뒤 항성 변환
    houses_placidus, ascmc = swe.houses(jd, lat, geo_lon, b'P')
    asc_tropical = ascmc[0]
    asc_sidereal = tropical_to_sidereal(asc_tropical, ayanamsa)
    lagna_rashi = int(asc_sidereal / 30) % 12

    # 행성 계산
    calc_flag = swe.FLG_SPEED
    planet_data = []

    for pid, name_en, name_kr in PLANETS:
        result = swe.calc_ut(jd, pid, calc_flag)
        trop_lon = result[0][0]
        speed = result[0][3]
        sid_lon = tropical_to_sidereal(trop_lon, ayanamsa)
        retrograde = speed < 0

        rashi_idx, deg, min_ = deg_to_rashi(sid_lon)
        nak_idx, pada, _ = get_nakshatra(sid_lon)
        nav_rashi = get_navamsha_rashi(sid_lon)
        dignity = get_dignity(name_en, rashi_idx)

        # 하우스 번호 (whole sign: 라그나 라시 = 1하우스)
        house = ((rashi_idx - lagna_rashi) % 12) + 1

        p = {
            "id": pid,
            "name_en": name_en,
            "name_kr": name_kr,
            "trop_longitude": trop_lon,
            "sid_longitude": sid_lon,
            "speed": speed,
            "retrograde": retrograde,
            "rashi_idx": rashi_idx,
            "rashi_en": RASHIS[rashi_idx][0],
            "rashi_kr": RASHIS[rashi_idx][1],
            "deg": deg,
            "min": min_,
            "nakshatra_idx": nak_idx,
            "nakshatra_en": NAKSHATRAS[nak_idx][0],
            "nakshatra_kr": NAKSHATRAS[nak_idx][1],
            "nakshatra_lord": NAKSHATRAS[nak_idx][2],
            "pada": pada,
            "navamsha_rashi": nav_rashi,
            "navamsha_en": RASHIS[nav_rashi][0],
            "navamsha_kr": RASHIS[nav_rashi][1],
            "dignity": dignity,
            "house": house,
        }
        planet_data.append(p)

    # 케투 = 라후 + 180°
    rahu_data = planet_data[-1]  # 마지막이 Rahu
    ketu_trop = (rahu_data["trop_longitude"] + 180) % 360
    ketu_sid = tropical_to_sidereal(ketu_trop, ayanamsa)
    ketu_rashi_idx, ketu_deg, ketu_min = deg_to_rashi(ketu_sid)
    ketu_nak_idx, ketu_pada, _ = get_nakshatra(ketu_sid)
    ketu_nav = get_navamsha_rashi(ketu_sid)
    ketu_dignity = get_dignity("Ketu", ketu_rashi_idx)
    ketu_house = ((ketu_rashi_idx - lagna_rashi) % 12) + 1

    planet_data.append({
        "id": -1,
        "name_en": "Ketu",
        "name_kr": "케투(남교점)",
        "trop_longitude": ketu_trop,
        "sid_longitude": ketu_sid,
        "speed": rahu_data["speed"],
        "retrograde": True,
        "rashi_idx": ketu_rashi_idx,
        "rashi_en": RASHIS[ketu_rashi_idx][0],
        "rashi_kr": RASHIS[ketu_rashi_idx][1],
        "deg": ketu_deg,
        "min": ketu_min,
        "nakshatra_idx": ketu_nak_idx,
        "nakshatra_en": NAKSHATRAS[ketu_nak_idx][0],
        "nakshatra_kr": NAKSHATRAS[ketu_nak_idx][1],
        "nakshatra_lord": NAKSHATRAS[ketu_nak_idx][2],
        "pada": ketu_pada,
        "navamsha_rashi": ketu_nav,
        "navamsha_en": RASHIS[ketu_nav][0],
        "navamsha_kr": RASHIS[ketu_nav][1],
        "dignity": ketu_dignity,
        "house": ketu_house,
    })

    # 다샤 계산 (달 기준)
    moon_data = planet_data[1]  # Moon
    dashas, birth_nak = calculate_dasha(moon_data["sid_longitude"], jd)

    # 요가 검출
    yogas = detect_yogas(planet_data, lagna_rashi)

    # 바바(하우스) 요약
    bhavas = {}
    for i in range(1, 13):
        bhava_rashi = (lagna_rashi + i - 1) % 12
        planets_in = [p for p in planet_data if p["house"] == i]
        bhavas[i] = {
            "rashi_idx": bhava_rashi,
            "rashi_en": RASHIS[bhava_rashi][0],
            "rashi_kr": RASHIS[bhava_rashi][1],
            "meaning": BHAVA_MEANINGS[i],
            "planets": planets_in,
        }

    return {
        "planets": planet_data,
        "ayanamsa": ayanamsa,
        "lagna_sidereal": asc_sidereal,
        "lagna_rashi": lagna_rashi,
        "lagna_en": RASHIS[lagna_rashi][0],
        "lagna_kr": RASHIS[lagna_rashi][1],
        "dashas": dashas,
        "yogas": yogas,
        "bhavas": bhavas,
        "gender": gender,
        "jd": jd,
    }


# ─── 출력: 텍스트 ───

def print_chart(chart, name, date_str, time_str, place):
    """차트 결과를 텍스트 포맷으로 출력"""
    print("=" * 65)
    print(f"  조티샤 차트 — {name}")
    print(f"  생년월일: {date_str}  시간: {time_str} (KST)")
    print(f"  출생지: {place}")
    print(f"  아야남샤 (라히리): {chart['ayanamsa']:.4f}°")
    print(f"  라그나: {chart['lagna_en']} ({chart['lagna_kr']}) {deg_to_rashi(chart['lagna_sidereal'])[1]}°{deg_to_rashi(chart['lagna_sidereal'])[2]:02d}'")
    print("=" * 65)
    print()

    # 행성 배치
    print("─" * 65)
    print("  ■ 행성 배치 (라시 차트)")
    print("─" * 65)
    print(f"  {'행성':<22} {'라시':<22} {'도수':>8}  {'하우스':>4}  {'낙샤트라':<16} {'파다':>3}  {'존엄'}")
    print(f"  {'─'*22} {'─'*22} {'─'*8}  {'─'*4}  {'─'*16} {'─'*3}  {'─'*12}")
    for p in chart["planets"]:
        label = f"{p['name_en']} ({p['name_kr']})"
        rashi = f"{p['rashi_en']} ({p['rashi_kr']})"
        pos = f"{p['deg']}°{p['min']:02d}'"
        nak = f"{p['nakshatra_en']}"
        retro = " (R)" if p["retrograde"] else ""
        dignity = p["dignity"]
        print(f"  {label:<22} {rashi:<22} {pos:>8}  {p['house']:>4}  {nak:<16} {p['pada']:>3}  {dignity}{retro}")
    print()

    # 나바암샤
    print("─" * 65)
    print("  ■ 나바암샤 (D-9) 배치")
    print("─" * 65)
    for p in chart["planets"]:
        label = f"{p['name_en']} ({p['name_kr']})"
        nav = f"{p['navamsha_en']} ({p['navamsha_kr']})"
        print(f"  {label:<22} → {nav}")
    print()

    # 바바 요약
    print("─" * 65)
    print("  ■ 바바 (하우스) 요약")
    print("─" * 65)
    for i in range(1, 13):
        b = chart["bhavas"][i]
        planets_str = ", ".join([p["name_en"] for p in b["planets"]]) if b["planets"] else "—"
        print(f"  {i:>2}하우스 ({b['meaning']:<18}) | {b['rashi_en']:<14} | {planets_str}")
    print()

    # 요가
    if chart["yogas"]:
        print("─" * 65)
        print("  ■ 검출된 요가")
        print("─" * 65)
        for y in chart["yogas"]:
            print(f"  ▸ {y['name']}")
            print(f"    {y['desc']}")
            print(f"    관련 행성: {y['planets']}")
            print()

    # 다샤
    print("─" * 65)
    print("  ■ 비무샤뜨리 마하다샤")
    print("─" * 65)
    now = datetime.now()
    for d in chart["dashas"][:12]:  # 최대 12개
        start = d["start"].strftime("%Y.%m")
        end = d["end"].strftime("%Y.%m")
        years = d["remaining"] if d["is_first"] else d["years"]
        current = " ◀ 현재" if d["start"] <= now <= d["end"] else ""
        print(f"  {d['lord']:<6} 다샤  {start} ~ {end}  ({years:.1f}년){current}")
    print()

    print("=" * 65)
    print("  ※ 아야남샤: 라히리 (Lahiri / Chitrapaksha)")
    print("  ※ 하우스: Whole Sign (라그나 라시 = 1하우스)")
    print("  ※ 시간대: KST (UTC+9)")
    print("  ※ 천문력: Swiss Ephemeris")
    print("=" * 65)


# ─── 출력: 마크다운 ───

def print_markdown(chart, name, date_str, time_str, place):
    """마크다운 형식 출력"""
    print()
    print("# 조티샤 정보")
    print()
    print("## 출생 정보")
    print()
    print(f"- **이름**: {name}")
    print(f"- **생년월일**: {date_str}")
    print(f"- **출생 시간**: {time_str} (KST)")
    print(f"- **출생지**: {place}")
    print(f"- **아야남샤 (라히리)**: {chart['ayanamsa']:.4f}°")
    print(f"- **라그나 (상승궁)**: {chart['lagna_en']} ({chart['lagna_kr']}) {deg_to_rashi(chart['lagna_sidereal'])[1]}°{deg_to_rashi(chart['lagna_sidereal'])[2]:02d}'")
    print(f"- **데이터 출처**: vedic_chart.py (Swiss Ephemeris, Lahiri Ayanamsa)")
    print()

    # 라시 차트
    print("## 라시 차트 (D-1) — 행성 배치")
    print()
    print("| 행성 | 라시 | 도수 | 하우스 | 낙샤트라 | 파다 | 존엄 | 비고 |")
    print("|------|------|------|--------|----------|------|------|------|")
    for p in chart["planets"]:
        retro = "역행(R)" if p["retrograde"] else ""
        print(f"| {p['name_en']} ({p['name_kr']}) | {p['rashi_en']} ({p['rashi_kr']}) | {p['deg']}°{p['min']:02d}' | {p['house']}하우스 | {p['nakshatra_en']} ({p['nakshatra_kr']}) | {p['pada']} | {p['dignity']} | {retro} |")
    print()

    # 나바암샤
    print("## 나바암샤 차트 (D-9)")
    print()
    print("| 행성 | 라시(D-1) | 나바암샤(D-9) |")
    print("|------|----------|--------------|")
    for p in chart["planets"]:
        print(f"| {p['name_en']} ({p['name_kr']}) | {p['rashi_en']} | {p['navamsha_en']} ({p['navamsha_kr']}) |")
    print()

    # 바바 요약
    print("## 바바 (하우스) 요약")
    print()
    print("| 하우스 | 의미 | 라시 | 재실 행성 |")
    print("|--------|------|------|-----------|")
    for i in range(1, 13):
        b = chart["bhavas"][i]
        planets_str = ", ".join([f"{p['name_en']}({p['name_kr']})" for p in b["planets"]]) if b["planets"] else "—"
        print(f"| {i}하우스 | {b['meaning']} | {b['rashi_en']} ({b['rashi_kr']}) | {planets_str} |")
    print()

    # 요가
    if chart["yogas"]:
        print("## 검출된 요가 (Yoga)")
        print()
        for y in chart["yogas"]:
            print(f"### {y['name']}")
            print(f"- **관련 행성**: {y['planets']}")
            print(f"- **구조**: {y['desc']}")
            print()

    # 다샤
    print("## 비무샤뜨리 마하다샤 (Vimshottari Dasha)")
    print()
    print("| 다샤 주(Lord) | 기간 | 시작 | 종료 | 비고 |")
    print("|---------------|------|------|------|------|")
    now = datetime.now()
    for d in chart["dashas"][:12]:
        start = d["start"].strftime("%Y.%m")
        end = d["end"].strftime("%Y.%m")
        years = d["remaining"] if d["is_first"] else d["years"]
        current = "◀ **현재 다샤**" if d["start"] <= now <= d["end"] else ""
        first_note = "(출생 시점 잔여)" if d["is_first"] else ""
        print(f"| {d['lord']} | {years:.1f}년 {first_note} | {start} | {end} | {current} |")
    print()

    print("---")
    print("- 아야남샤: 라히리 (Lahiri / Chitrapaksha)")
    print("- 하우스 시스템: Whole Sign (라그나 라시 = 1하우스)")
    print("- 시간대: KST (UTC+9)")
    print("- 천문력: Swiss Ephemeris")


# ─── CLI ───

def parse_args():
    parser = argparse.ArgumentParser(
        description="조티샤 차트 생성기 (Swiss Ephemeris + Lahiri Ayanamsa)"
    )
    parser.add_argument("--name", type=str, help="이름")
    parser.add_argument("--date", type=str, help="생년월일 (YYYY-MM-DD)")
    parser.add_argument("--time", type=str, help="출생 시간 (HH:MM, KST)")
    parser.add_argument("--place", type=str, help="출생 장소 (한국 도시명)")
    parser.add_argument("--lat", type=float, help="위도 (직접 지정)")
    parser.add_argument("--lon", type=float, help="경도 (직접 지정)")
    parser.add_argument("--gender", type=str, choices=["M", "F"], default="M",
                        help="성별 (M/F)")
    parser.add_argument("--markdown", action="store_true",
                        help="마크다운 형식으로 출력")
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.date or not args.time or not args.name:
        print("사용법: python3 vedic_chart.py --name 이름 --date YYYY-MM-DD --time HH:MM --place 도시명 --gender M/F")
        print()
        print("예시:")
        print("  python3 vedic_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --place 창원 --gender M")
        print("  python3 vedic_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --place 서울 --gender M --markdown")
        print()
        print("지원 도시:", ", ".join(sorted(CITY_COORDS.keys())))
        sys.exit(1)

    # 날짜 파싱
    dt = datetime.strptime(args.date, "%Y-%m-%d")
    year, month, day = dt.year, dt.month, dt.day

    # 시간 파싱
    time_parts = args.time.split(":")
    hour = int(time_parts[0])
    minute = int(time_parts[1]) if len(time_parts) > 1 else 0

    # 좌표
    if args.lat is not None and args.lon is not None:
        lat, lon = args.lat, args.lon
        place = args.place or f"{lat:.4f}N, {lon:.4f}E"
    elif args.place:
        # 영문 → 한글 변환, "성남시" → "성남", "서울특별시" → "서울" 등 정규화
        import re
        place_input = args.place.strip()
        en_mapped = CITY_NAME_EN.get(place_input.lower())
        if en_mapped:
            place_input = en_mapped
        normalized = re.sub(r'(특별자치시|특별자치도|특별시|광역시|시|군|구)$', '', place_input)
        place_key = normalized if normalized in CITY_COORDS else place_input
        if place_key in CITY_COORDS:
            lat, lon = CITY_COORDS[place_key]
            place = f"{place_key} (대한민국)"
        else:
            print(f"오류: '{args.place}' 도시를 찾을 수 없습니다.")
            print(f"지원 도시: {', '.join(sorted(CITY_COORDS.keys()))}")
            print("직접 좌표를 지정하려면 --lat, --lon 옵션을 사용하세요.")
            sys.exit(1)
    else:
        print("오류: --place 또는 --lat/--lon을 지정해야 합니다.")
        sys.exit(1)

    # 계산
    chart = calculate_chart(year, month, day, hour, minute, lat, lon, args.gender)

    # 출력
    if args.markdown:
        print_markdown(chart, args.name, args.date, args.time, place)
    else:
        print_chart(chart, args.name, args.date, args.time, place)


if __name__ == "__main__":
    main()
