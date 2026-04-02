#!/usr/bin/env python3
"""
astro_chart.py - 서양 점성술 네이탈 차트 생성기
Swiss Ephemeris 기반으로 행성 배치, 하우스, 어스펙트를 계산한다.

사용법:
    python3 astro_chart.py                                          # contexts/ 폴더 인물 선택
    python3 astro_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --place "창원"
    python3 astro_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --lat 35.228 --lon 128.681

의존 패키지:
    pip3 install pyswisseph
"""

import sys
import argparse
import math
from datetime import datetime

try:
    import swisseph as swe
except ImportError:
    print("오류: pyswisseph 패키지가 필요합니다.")
    print("설치: pip3 install pyswisseph")
    sys.exit(1)

# ─── 상수 ───

SIGNS = [
    ("Aries", "양"),
    ("Taurus", "황소"),
    ("Gemini", "쌍둥이"),
    ("Cancer", "게"),
    ("Leo", "사자"),
    ("Virgo", "처녀"),
    ("Libra", "천칭"),
    ("Scorpio", "전갈"),
    ("Sagittarius", "사수"),
    ("Capricorn", "염소"),
    ("Aquarius", "물병"),
    ("Pisces", "물고기"),
]

PLANETS = [
    (swe.SUN, "Sun", "태양"),
    (swe.MOON, "Moon", "달"),
    (swe.MERCURY, "Mercury", "수성"),
    (swe.VENUS, "Venus", "금성"),
    (swe.MARS, "Mars", "화성"),
    (swe.JUPITER, "Jupiter", "목성"),
    (swe.SATURN, "Saturn", "토성"),
    (swe.URANUS, "Uranus", "천왕성"),
    (swe.NEPTUNE, "Neptune", "해왕성"),
    (swe.PLUTO, "Pluto", "명왕성"),
]

# 소행성/감응점
EXTRAS = [
    (swe.MEAN_NODE, "North Node", "북교점"),
    (swe.MEAN_APOG, "Lilith", "릴리스"),
    (swe.CHIRON, "Chiron", "키론"),
]

ASPECTS = [
    ("Conjunction", "합", 0, 8),
    ("Opposition", "충", 180, 8),
    ("Trine", "삼합", 120, 8),
    ("Square", "사각", 90, 7),
    ("Sextile", "육분합", 60, 6),
]

ELEMENTS = {
    "Aries": "불(Fire)", "Leo": "불(Fire)", "Sagittarius": "불(Fire)",
    "Taurus": "흙(Earth)", "Virgo": "흙(Earth)", "Capricorn": "흙(Earth)",
    "Gemini": "바람(Air)", "Libra": "바람(Air)", "Aquarius": "바람(Air)",
    "Cancer": "물(Water)", "Scorpio": "물(Water)", "Pisces": "물(Water)",
}

MODALITIES = {
    "Aries": "Cardinal(활동궁)", "Cancer": "Cardinal(활동궁)",
    "Libra": "Cardinal(활동궁)", "Capricorn": "Cardinal(활동궁)",
    "Taurus": "Fixed(고정궁)", "Leo": "Fixed(고정궁)",
    "Scorpio": "Fixed(고정궁)", "Aquarius": "Fixed(고정궁)",
    "Gemini": "Mutable(변통궁)", "Virgo": "Mutable(변통궁)",
    "Sagittarius": "Mutable(변통궁)", "Pisces": "Mutable(변통궁)",
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

def deg_to_sign(longitude):
    """경도(0~360) → (별자리 인덱스, 도, 분)"""
    sign_idx = int(longitude / 30)
    deg_in_sign = longitude - sign_idx * 30
    degrees = int(deg_in_sign)
    minutes = int((deg_in_sign - degrees) * 60)
    return sign_idx, degrees, minutes


def format_pos(longitude):
    """경도 → '별자리 도°분'' 문자열"""
    sign_idx, deg, min_ = deg_to_sign(longitude)
    sign_en, sign_kr = SIGNS[sign_idx]
    return f"{sign_en} ({sign_kr}) {deg}°{min_:02d}'"


def format_pos_short(longitude):
    """경도 → '별자리 도°분'' (영문만)"""
    sign_idx, deg, min_ = deg_to_sign(longitude)
    sign_en, _ = SIGNS[sign_idx]
    return f"{sign_en} {deg}°{min_:02d}'"


def get_house(longitude, house_cusps):
    """행성 경도가 속하는 하우스 번호 반환 (1~12)"""
    for i in range(12):
        cusp_start = house_cusps[i]
        cusp_end = house_cusps[(i + 1) % 12]
        if cusp_start < cusp_end:
            if cusp_start <= longitude < cusp_end:
                return i + 1
        else:  # 0도 경계를 넘는 경우
            if longitude >= cusp_start or longitude < cusp_end:
                return i + 1
    return 1


def angle_diff(a, b):
    """두 경도의 최소 각도 차이 (0~180)"""
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


def find_aspects(bodies, orb_factor=1.0):
    """행성 쌍의 어스펙트 검출"""
    results = []
    names = list(bodies.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            lon1, lon2 = bodies[n1], bodies[n2]
            diff = angle_diff(lon1, lon2)
            for asp_name, asp_kr, asp_angle, max_orb in ASPECTS:
                orb = abs(diff - asp_angle)
                if orb <= max_orb * orb_factor:
                    # Applying vs Separating 판단 (간략)
                    results.append({
                        "body1": n1,
                        "body2": n2,
                        "aspect": asp_name,
                        "aspect_kr": asp_kr,
                        "angle": asp_angle,
                        "orb": orb,
                    })
                    break
    return results


def calculate_fortune(asc_lon, sun_lon, moon_lon):
    """Part of Fortune 계산: ASC + Moon - Sun"""
    fortune = (asc_lon + moon_lon - sun_lon) % 360
    return fortune


# ─── 메인 계산 ───

def calculate_whole_sign_houses(asc):
    """Whole Sign 하우스 계산: ASC가 속한 별자리 = 1하우스, 이후 별자리 순서대로"""
    asc_sign_idx = int(asc / 30)
    house_cusps = []
    for i in range(12):
        sign_idx = (asc_sign_idx + i) % 12
        house_cusps.append(sign_idx * 30.0)
    return house_cusps


def calculate_chart(year, month, day, hour, minute, lat, geo_lon, house_system="placidus"):
    """네이탈 차트 전체 계산"""
    # Swiss Ephemeris 데이터 파일 경로 (키론 등 소행성 계산에 필요)
    import os
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

    # 행성 계산 (Swiss Ephemeris 데이터 파일 사용, 없으면 Moshier 폴백)
    calc_flag = swe.FLG_SPEED
    planet_data = []
    for pid, name_en, name_kr in PLANETS:
        result = swe.calc_ut(jd, pid, calc_flag)
        lon = result[0][0]
        speed = result[0][3]
        retrograde = speed < 0
        planet_data.append({
            "id": pid,
            "name_en": name_en,
            "name_kr": name_kr,
            "longitude": lon,
            "speed": speed,
            "retrograde": retrograde,
        })

    # 감응점 계산 (키론은 외부 천문력 필요 — 실패 시 건너뜀)
    extra_data = []
    for pid, name_en, name_kr in EXTRAS:
        try:
            result = swe.calc_ut(jd, pid, calc_flag)
            lon = result[0][0]
            speed = result[0][3]
            retrograde = speed < 0
            extra_data.append({
                "id": pid,
                "name_en": name_en,
                "name_kr": name_kr,
                "longitude": lon,
                "speed": speed,
                "retrograde": retrograde,
            })
        except swe.Error:
            print(f"  ※ {name_en} ({name_kr}): 외부 천문력 파일 없음 — 생략")

    # 하우스 계산 — Placidus로 ASC/MC를 구하고, 하우스 시스템에 따라 분기
    houses_placidus, ascmc = swe.houses(jd, lat, geo_lon, b'P')
    asc = ascmc[0]
    mc = ascmc[1]

    if house_system == "wholesign":
        house_cusps = calculate_whole_sign_houses(asc)
        house_system_name = "Whole Sign"
    else:
        house_cusps = list(houses_placidus)
        house_system_name = "Placidus"

    # 하우스 배치
    for p in planet_data:
        p["house"] = get_house(p["longitude"], house_cusps)
    for p in extra_data:
        p["house"] = get_house(p["longitude"], house_cusps)

    # Part of Fortune
    sun_lon = planet_data[0]["longitude"]
    moon_lon = planet_data[1]["longitude"]
    fortune_lon = calculate_fortune(asc, sun_lon, moon_lon)

    # Vertex (7th house cusp의 반대편 - 간략 계산)
    # Vertex = ASC of the chart if born at the IC latitude
    # 정확한 Vertex는 별도 계산 필요, 여기선 swe의 ascmc[3] 사용
    vertex = ascmc[3]

    # 어스펙트 계산
    all_bodies = {}
    for p in planet_data:
        all_bodies[f"{p['name_en']} ({p['name_kr']})"] = p["longitude"]

    planet_aspects = find_aspects(all_bodies)

    # 앵글·노드 포함 어스펙트
    angle_bodies = dict(all_bodies)
    for p in extra_data:
        angle_bodies[f"{p['name_en']} ({p['name_kr']})"] = p["longitude"]
    angle_bodies["ASC (상승궁)"] = asc
    angle_bodies["MC (중천)"] = mc
    angle_bodies["DSC (하강궁)"] = (asc + 180) % 360
    angle_bodies["IC (천저)"] = (mc + 180) % 360

    all_aspects = find_aspects(angle_bodies, orb_factor=1.0)

    # 원소/모달리티 분포
    element_count = {"불(Fire)": [], "흙(Earth)": [], "바람(Air)": [], "물(Water)": []}
    modality_count = {"Cardinal(활동궁)": [], "Fixed(고정궁)": [], "Mutable(변통궁)": []}

    for p in planet_data:
        sign_idx = int(p["longitude"] / 30)
        sign_en = SIGNS[sign_idx][0]
        elem = ELEMENTS.get(sign_en, "")
        mod = MODALITIES.get(sign_en, "")
        if elem:
            element_count[elem].append(p["name_en"])
        if mod:
            modality_count[mod].append(p["name_en"])

    return {
        "planets": planet_data,
        "extras": extra_data,
        "houses": house_cusps,
        "house_system": house_system_name,
        "asc": asc,
        "mc": mc,
        "dsc": (asc + 180) % 360,
        "ic": (mc + 180) % 360,
        "fortune": fortune_lon,
        "vertex": vertex,
        "planet_aspects": planet_aspects,
        "all_aspects": all_aspects,
        "elements": element_count,
        "modalities": modality_count,
    }


# ─── 출력 ───

def print_chart(chart, name, date_str, time_str, place):
    """차트 결과를 포맷팅하여 출력"""
    print("=" * 60)
    print(f"  서양 점성술 네이탈 차트")
    print(f"  이름: {name}")
    print(f"  생년월일: {date_str}  시간: {time_str} (KST)")
    print(f"  출생지: {place}")
    print("=" * 60)
    print()

    # 행성 배치
    print("─" * 60)
    print("  ■ 행성 배치 (Planet Positions)")
    print("─" * 60)
    print(f"  {'행성':<22} {'별자리':<28} {'하우스':>6}  {'비고'}")
    print(f"  {'─'*22} {'─'*28} {'─'*6}  {'─'*10}")
    for p in chart["planets"]:
        retro = "Retrograde" if p["retrograde"] else ""
        pos = format_pos(p["longitude"])
        label = f"{p['name_en']} ({p['name_kr']})"
        print(f"  {label:<22} {pos:<28} {p['house']:>4}th  {retro}")
    print()

    # 감응점
    print("─" * 60)
    print("  ■ 감응점 (Sensitive Points)")
    print("─" * 60)
    for p in chart["extras"]:
        retro = "Retrograde" if p["retrograde"] else ""
        pos = format_pos(p["longitude"])
        label = f"{p['name_en']} ({p['name_kr']})"
        house = p["house"]
        print(f"  {label:<22} {pos:<28} {house:>4}th  {retro}")

    fortune_pos = format_pos(chart["fortune"])
    fortune_house = get_house(chart["fortune"], chart["houses"])
    print(f"  {'Fortune (포춘)':<22} {fortune_pos:<28} {fortune_house:>4}th")

    vertex_pos = format_pos(chart["vertex"])
    vertex_house = get_house(chart["vertex"], chart["houses"])
    print(f"  {'Vertex (버텍스)':<22} {vertex_pos:<28} {vertex_house:>4}th")
    print()

    # 앵글
    print("─" * 60)
    print("  ■ 앵글 (Angles)")
    print("─" * 60)
    print(f"  ASC (상승궁):  {format_pos(chart['asc'])}")
    print(f"  MC  (중천):    {format_pos(chart['mc'])}")
    print(f"  DSC (하강궁):  {format_pos(chart['dsc'])}")
    print(f"  IC  (천저):    {format_pos(chart['ic'])}")
    print()

    # 하우스
    print("─" * 60)
    print(f"  ■ 하우스 커스프 ({chart['house_system']})")
    print("─" * 60)
    for i, cusp in enumerate(chart["houses"]):
        ordinal = f"{i+1}th" if i + 1 not in (1, 2, 3) else f"{i+1}{'st' if i+1==1 else 'nd' if i+1==2 else 'rd'}"
        print(f"  {ordinal:>5} House:  {format_pos_short(cusp)}")
    print()

    # 주요 행성 어스펙트
    print("─" * 60)
    print("  ■ 주요 행성 어스펙트 (Planet Aspects)")
    print("─" * 60)
    for asp in chart["planet_aspects"]:
        print(f"  {asp['body1']:<24} {asp['aspect']:<14} {asp['body2']:<24} (Orb: {asp['orb']:.2f}°)")
    print()

    # 원소 분포
    print("─" * 60)
    print("  ■ 원소 분포 (Elements)")
    print("─" * 60)
    for elem, planets in chart["elements"].items():
        bar = "●" * len(planets) + "○" * (10 - len(planets))
        names = ", ".join(planets) if planets else "-"
        print(f"  {elem:<12} {bar} {len(planets)}  ({names})")
    print()

    # 모달리티 분포
    print("─" * 60)
    print("  ■ 모달리티 분포 (Modalities)")
    print("─" * 60)
    for mod, planets in chart["modalities"].items():
        bar = "●" * len(planets) + "○" * (10 - len(planets))
        names = ", ".join(planets) if planets else "-"
        print(f"  {mod:<22} {bar} {len(planets)}  ({names})")
    print()

    print("=" * 60)
    print(f"  ※ 하우스 시스템: {chart['house_system']}")
    print("  ※ 시간대: KST (UTC+9)")
    print("  ※ 천문력: Swiss Ephemeris")
    print("=" * 60)


def print_markdown(chart, name, date_str, time_str, place):
    """contexts 파일에 붙여넣기 가능한 마크다운 형식 출력"""
    print()
    print("# 점성술 정보")
    print()
    print("## 출생 정보 (점성술용)")
    print()
    print(f"- **생년월일**: {date_str}")
    print(f"- **출생 시간**: {time_str}")
    print(f"- **출생 장소**: {place}")
    print(f"- **데이터 출처**: astro_chart.py (Swiss Ephemeris)")
    print()

    # 행성 배치 테이블
    print("## 네이탈 차트 - 행성 배치")
    print()
    print("| 행성 | 별자리 | 도수 | 하우스 | 비고 |")
    print("|------|--------|------|--------|------|")
    for p in chart["planets"]:
        sign_idx, deg, min_ = deg_to_sign(p["longitude"])
        sign_en, sign_kr = SIGNS[sign_idx]
        retro = "Retrograde (역행)" if p["retrograde"] else ""
        print(f"| {p['name_en']} ({p['name_kr']}) | {sign_en} ({sign_kr}) | {deg}°{min_:02d}' | {p['house']}th | {retro} |")
    print()

    # 감응점
    print("## 감응점 (Sensitive Points)")
    print()
    print("| 포인트 | 별자리 | 도수 | 하우스 | 비고 |")
    print("|--------|--------|------|--------|------|")
    for p in chart["extras"]:
        sign_idx, deg, min_ = deg_to_sign(p["longitude"])
        sign_en, sign_kr = SIGNS[sign_idx]
        retro = "Retrograde" if p["retrograde"] else ""
        print(f"| {p['name_en']} ({p['name_kr']}) | {sign_en} ({sign_kr}) | {deg}°{min_:02d}' | {p['house']}th | {retro} |")

    # Fortune
    sign_idx, deg, min_ = deg_to_sign(chart["fortune"])
    sign_en, sign_kr = SIGNS[sign_idx]
    fortune_house = get_house(chart["fortune"], chart["houses"])
    print(f"| Fortune (포춘) | {sign_en} ({sign_kr}) | {deg}°{min_:02d}' | {fortune_house}th | |")

    # Vertex
    sign_idx, deg, min_ = deg_to_sign(chart["vertex"])
    sign_en, sign_kr = SIGNS[sign_idx]
    vertex_house = get_house(chart["vertex"], chart["houses"])
    print(f"| Vertex (버텍스) | {sign_en} ({sign_kr}) | {deg}°{min_:02d}' | {vertex_house}th | |")
    print()

    # 앵글
    print("## 앵글 (Angles)")
    print()
    print("| 포인트 | 별자리 | 도수 |")
    print("|--------|--------|------|")
    for label, lon in [("ASC (상승궁)", chart["asc"]), ("MC (중천)", chart["mc"]),
                       ("DSC (하강궁)", chart["dsc"]), ("IC (천저)", chart["ic"])]:
        sign_idx, deg, min_ = deg_to_sign(lon)
        sign_en, sign_kr = SIGNS[sign_idx]
        print(f"| {label} | {sign_en} ({sign_kr}) | {deg}°{min_:02d}' |")
    print()

    # 하우스
    print(f"## 하우스 배치 ({chart['house_system']})")
    print()
    print("| 하우스 | 별자리 | 도수 |")
    print("|--------|--------|------|")
    for i, cusp in enumerate(chart["houses"]):
        sign_idx, deg, min_ = deg_to_sign(cusp)
        sign_en, sign_kr = SIGNS[sign_idx]
        print(f"| {i+1}th | {sign_en} ({sign_kr}) | {deg}°{min_:02d}' |")
    print()

    # 어스펙트
    print("## 주요 행성 어스펙트")
    print()
    print("| 행성 1 | 어스펙트 | 행성 2 | 오브 |")
    print("|--------|----------|--------|------|")
    for asp in chart["planet_aspects"]:
        print(f"| {asp['body1']} | {asp['aspect']} ({asp['angle']}°) | {asp['body2']} | {asp['orb']:.2f}° |")
    print()

    # 원소
    print("## 원소·모달리티 분포")
    print()
    print("### 원소 (Element)")
    print("| 원소 | 행성 |")
    print("|------|------|")
    for elem, planets in chart["elements"].items():
        names = ", ".join(planets) if planets else "-"
        print(f"| {elem} | {names} |")
    print()

    print("### 모달리티 (Modality)")
    print("| 모달리티 | 행성 |")
    print("|----------|------|")
    for mod, planets in chart["modalities"].items():
        names = ", ".join(planets) if planets else "-"
        print(f"| {mod} | {names} |")


# ─── CLI ───

def parse_args():
    parser = argparse.ArgumentParser(
        description="서양 점성술 네이탈 차트 생성기 (Swiss Ephemeris 기반)"
    )
    parser.add_argument("--name", type=str, help="이름")
    parser.add_argument("--date", type=str, help="생년월일 (YYYY-MM-DD)")
    parser.add_argument("--time", type=str, help="출생 시간 (HH:MM, KST)")
    parser.add_argument("--place", type=str, help="출생 장소 (한국 도시명)")
    parser.add_argument("--lat", type=float, help="위도 (직접 지정)")
    parser.add_argument("--lon", type=float, help="경도 (직접 지정)")
    parser.add_argument("--markdown", action="store_true",
                        help="마크다운 형식으로 출력 (contexts 파일용)")
    parser.add_argument("--house", type=str, default="placidus",
                        choices=["placidus", "wholesign"],
                        help="하우스 시스템 (기본: placidus)")
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.date or not args.time or not args.name:
        print("사용법: python3 astro_chart.py --name 이름 --date YYYY-MM-DD --time HH:MM --place 도시명")
        print()
        print("예시:")
        print("  python3 astro_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --place 창원")
        print("  python3 astro_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --lat 35.228 --lon 128.681")
        print("  python3 astro_chart.py --name 홍길동 --date 1983-02-26 --time 19:58 --place 창원 --markdown")
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
    chart = calculate_chart(year, month, day, hour, minute, lat, lon, args.house)

    # 출력
    if args.markdown:
        print_markdown(chart, args.name, args.date, args.time, place)
    else:
        print_chart(chart, args.name, args.date, args.time, place)


if __name__ == "__main__":
    main()
