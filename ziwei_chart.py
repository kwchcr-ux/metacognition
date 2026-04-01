#!/usr/bin/env python3
"""
ziwei_chart.py - 자미두수(紫微斗數) 명반 생성기
출생 정보를 입력하면 12궁 배치, 주성·보성·살성, 사화, 대한을 계산한다.

사용법:
    python3 ziwei_chart.py --name 이름 --date 1986-02-06 --time 17:57 --gender F
    python3 ziwei_chart.py --name 이름 --date 1986-02-06 --time 17:57 --gender F --markdown
    python3 ziwei_chart.py --name 이름 --date 1985-12-28 --time 17:57 --gender F --lunar

의존 패키지:
    pip3 install lunardate
"""

import sys
import argparse
from datetime import datetime

try:
    from lunardate import LunarDate
except ImportError:
    print("오류: lunardate 패키지가 필요합니다.")
    print("설치: pip3 install lunardate")
    print("또는 --lunar 옵션으로 음력 날짜를 직접 입력하세요.")
    sys.exit(1)


# ═══════════════════════════════════════════════════
#  상수
# ═══════════════════════════════════════════════════

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEMS_KR = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
BRANCHES_KR = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

PALACE_NAMES = [
    "命宮", "兄弟", "夫妻", "子女", "財帛", "疾厄",
    "遷移", "交友", "官祿", "田宅", "福德", "父母",
]
PALACE_NAMES_KR = [
    "명궁", "형제궁", "부처궁", "자녀궁", "재백궁", "질액궁",
    "천이궁", "교우궁", "관록궁", "전택궁", "복덕궁", "부모궁",
]

# 오행국 번호 → 이름
BUREAU_NAMES = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}

# 납음 오행 → 오행국 번호
NAYIN_BUREAU = {
    "水": 2, "木": 3, "金": 4, "土": 5, "火": 6,
}

# 납음 60갑자 배열 (30쌍, 각 쌍은 2개의 간지)
NAYIN_CYCLE = ["金", "火", "木", "土", "金", "火", "水", "土", "金", "木",
               "水", "土", "火", "木", "水"]

NAYIN_NAMES = [
    "海中金", "爐中火", "大林木", "路旁土", "劍鋒金",
    "山頭火", "澗下水", "城頭土", "白蠟金", "楊柳木",
    "泉中水", "屋上土", "霹靂火", "松柏木", "長流水",
    "沙中金", "山下火", "平地木", "壁上土", "金箔金",
    "覆燈火", "天河水", "大驛土", "釵釧金", "桑拓木",
    "大溪水", "沙中土", "天上火", "石榴木", "大海水",
]


# ═══════════════════════════════════════════════════
#  주성 이름
# ═══════════════════════════════════════════════════

# 紫微 계열 (6성)
ZIWEI_SERIES = ["紫微", "天機", None, "太陽", "武曲", "天同", None, None, "廉貞"]
# 天府 계열 (8성) — 天府로부터 순행
TIANFU_SERIES = ["天府", "太陰", "貪狼", "巨門", "天相", "天梁", "七殺",
                 None, None, None, "破軍"]

ALL_MAIN_STARS = [
    "紫微", "天機", "太陽", "武曲", "天同", "廉貞",
    "天府", "太陰", "貪狼", "巨門", "天相", "天梁", "七殺", "破軍",
]


# ═══════════════════════════════════════════════════
#  묘왕이함 (밝기) 테이블
# ═══════════════════════════════════════════════════
#  인덱스: 0=子, 1=丑, ..., 11=亥

BRIGHTNESS = {
    "紫微": ["旺", "旺", "得", "利", "旺", "得", "旺", "旺", "得", "得", "旺", "得"],
    "天機": ["旺", "得", "旺", "廟", "旺", "平", "陷", "陷", "利", "平", "利", "旺"],
    "太陽": ["陷", "陷", "旺", "廟", "旺", "廟", "旺", "得", "利", "平", "陷", "陷"],
    "武曲": ["旺", "得", "利", "平", "廟", "陷", "利", "旺", "得", "旺", "廟", "得"],
    "天同": ["旺", "得", "平", "陷", "利", "廟", "陷", "得", "利", "廟", "陷", "旺"],
    "廉貞": ["平", "陷", "利", "平", "陷", "旺", "得", "廟", "廟", "旺", "得", "利"],
    "天府": ["廟", "旺", "得", "利", "平", "旺", "廟", "旺", "得", "利", "平", "旺"],
    "太陰": ["廟", "旺", "陷", "陷", "陷", "陷", "陷", "陷", "得", "旺", "廟", "廟"],
    "貪狼": ["旺", "陷", "廟", "陷", "旺", "陷", "平", "陷", "利", "旺", "旺", "平"],
    "巨門": ["旺", "陷", "利", "旺", "陷", "平", "旺", "陷", "利", "旺", "平", "陷"],
    "天相": ["廟", "得", "旺", "利", "得", "廟", "旺", "利", "利", "得", "廟", "旺"],
    "天梁": ["旺", "旺", "利", "得", "得", "廟", "廟", "利", "得", "旺", "旺", "利"],
    "七殺": ["旺", "得", "廟", "利", "旺", "得", "旺", "廟", "旺", "利", "廟", "得"],
    "破軍": ["旺", "陷", "得", "陷", "旺", "得", "旺", "陷", "得", "陷", "陷", "廟"],
}


# ═══════════════════════════════════════════════════
#  사화 테이블 (年干別)
# ═══════════════════════════════════════════════════
#  年干 index → [化祿, 化權, 化科, 化忌]

SIHUA = {
    0: ["廉貞", "破軍", "武曲", "太陽"],  # 甲
    1: ["天機", "天梁", "紫微", "太陰"],  # 乙
    2: ["天同", "天機", "文昌", "廉貞"],  # 丙
    3: ["太陰", "天同", "天機", "巨門"],  # 丁
    4: ["貪狼", "太陰", "右弼", "天機"],  # 戊
    5: ["武曲", "貪狼", "天梁", "文曲"],  # 己
    6: ["太陽", "武曲", "太陰", "天同"],  # 庚
    7: ["巨門", "太陽", "文曲", "文昌"],  # 辛
    8: ["天梁", "紫微", "左輔", "武曲"],  # 壬
    9: ["破軍", "巨門", "太陰", "貪狼"],  # 癸
}
SIHUA_NAMES = ["化祿", "化權", "化科", "化忌"]


# ═══════════════════════════════════════════════════
#  보조성 테이블
# ═══════════════════════════════════════════════════

# 天魁·天鉞 (年干別)
TIANKUI = {0: 1, 1: 0, 2: 11, 3: 11, 4: 1, 5: 0, 6: 1, 7: 6, 8: 3, 9: 3}
TIANYUE = {0: 7, 1: 8, 2: 9, 3: 9, 4: 7, 5: 8, 6: 7, 7: 2, 8: 5, 9: 5}

# 祿存 (年干別)
LUCUN = {0: 2, 1: 3, 2: 5, 3: 6, 4: 5, 5: 6, 6: 8, 7: 9, 8: 11, 9: 0}

# 火星 시작위치 (年支 그룹별)
#  寅午戌→丑, 申子辰→寅, 巳酉丑→卯, 亥卯未→酉
HUOXING_START = {
    "寅午戌": 1, "申子辰": 2, "巳酉丑": 3, "亥卯未": 9,
}

# 鈴星 시작위치 (年支 그룹별)
#  寅午戌→卯, 나머지→戌
LINGXING_START = {
    "寅午戌": 3, "申子辰": 10, "巳酉丑": 10, "亥卯未": 10,
}

# 年支 → 그룹명
BRANCH_GROUP = {
    2: "寅午戌", 6: "寅午戌", 10: "寅午戌",
    8: "申子辰", 0: "申子辰", 4: "申子辰",
    5: "巳酉丑", 9: "巳酉丑", 1: "巳酉丑",
    11: "亥卯未", 3: "亥卯未", 7: "亥卯未",
}

# 天馬 (年支別)
TIANMA = {
    2: 8, 6: 8, 10: 8,     # 寅午戌 → 申
    8: 2, 0: 2, 4: 2,       # 申子辰 → 寅
    5: 11, 9: 11, 1: 11,    # 巳酉丑 → 亥
    11: 5, 3: 5, 7: 5,      # 亥卯未 → 巳
}


# ═══════════════════════════════════════════════════
#  유틸리티
# ═══════════════════════════════════════════════════

def sexagenary_index(stem_idx, branch_idx):
    """천간·지지 인덱스 → 60갑자 인덱스"""
    return (36 * stem_idx + 25 * branch_idx) % 60


def nayin_bureau(stem_idx, branch_idx):
    """천간·지지 → 납음 오행국 번호 (2~6)"""
    idx = sexagenary_index(stem_idx, branch_idx)
    pair = idx // 2
    element = NAYIN_CYCLE[pair % 15]
    return NAYIN_BUREAU[element], NAYIN_NAMES[pair % 30], element


def hour_to_shichen(hour, minute=0):
    """시:분 → 시진 인덱스 (0=子, 1=丑, ..., 11=亥)"""
    # ※ 00:00(자정) 정각 출생 기록은 실제로는 거의 없음.
    #    병원 기록이 자정 전후를 반올림한 경우가 대부분이므로
    #    子時 경계(23:00/01:00)는 특히 주의가 필요.
    if hour >= 23 or hour < 1:
        return 0  # 子時
    return ((hour + 1) // 2) % 12


def is_shichen_boundary(hour, minute):
    """시진 경계 시간인지 판별. 경계면 (이전 시진, 다음 시진) 반환, 아니면 None."""
    if minute != 0:
        return None
    if hour % 2 != 1:
        return None
    # 홀수 정각 = 시진 경계
    # 이전 시진 (이 시간을 포함하는 앞쪽 시진)
    prev_shichen = (hour // 2) % 12
    # 다음 시진 (이 시간부터 시작하는 뒤쪽 시진)
    next_shichen = ((hour + 1) // 2) % 12
    return prev_shichen, next_shichen


def palace_stem(year_stem_idx, branch_idx):
    """오호둔법: 年干과 궁 地支 → 궁 天干 인덱스"""
    base = ((year_stem_idx % 5) * 2 + 2) % 10
    return (base + (branch_idx - 2) % 12) % 10


# ═══════════════════════════════════════════════════
#  명궁·신궁 계산
# ═══════════════════════════════════════════════════

def calc_mingong(lunar_month, shichen_idx):
    """명궁 지지 인덱스 계산"""
    return (1 + lunar_month - shichen_idx) % 12


def calc_shengong(lunar_month, shichen_idx):
    """신궁 지지 인덱스 계산"""
    return (1 + lunar_month + shichen_idx) % 12


# ═══════════════════════════════════════════════════
#  紫微 위치 계산 (핵심 알고리즘)
# ═══════════════════════════════════════════════════

def calc_ziwei_branch(lunar_day, bureau):
    """
    오행국과 음력 일수로 紫微星의 지지 위치를 계산한다.

    공식: floor(일수 / 국수) + 1
    丑(1)부터 시작하여 국수만큼의 일수마다 한 칸씩 전진한다.
    모든 오행국에 동일하게 적용된다.
    """
    return (lunar_day // bureau + 1) % 12


# ═══════════════════════════════════════════════════
#  주성 배치
# ═══════════════════════════════════════════════════

def place_main_stars(ziwei_branch):
    """紫微 위치로부터 14개 주성 배치 (branch_idx → star_name list)"""
    stars = {}  # branch_idx → [star_name, ...]

    # 紫微 계열: 紫微(0), 天機(-1), [空](-2), 太陽(-3), 武曲(-4), 天同(-5),
    #            [空](-6), [空](-7), 廉貞(-8)
    ziwei_offsets = {
        "紫微": 0, "天機": -1, "太陽": -3, "武曲": -4, "天同": -5, "廉貞": -8,
    }
    for name, offset in ziwei_offsets.items():
        br = (ziwei_branch + offset) % 12
        stars.setdefault(br, []).append(name)

    # 天府 위치: 紫微와 寅-申 축 대칭 → (4 - 紫微) mod 12
    tianfu_branch = (4 - ziwei_branch) % 12

    # 天府 계열: 天府(0), 太陰(+1), 貪狼(+2), 巨門(+3), 天相(+4),
    #            天梁(+5), 七殺(+6), [空](+7,+8,+9), 破軍(+10)
    tianfu_offsets = {
        "天府": 0, "太陰": 1, "貪狼": 2, "巨門": 3, "天相": 4,
        "天梁": 5, "七殺": 6, "破軍": 10,
    }
    for name, offset in tianfu_offsets.items():
        br = (tianfu_branch + offset) % 12
        stars.setdefault(br, []).append(name)

    return stars


# ═══════════════════════════════════════════════════
#  보조성 배치
# ═══════════════════════════════════════════════════

def place_auxiliary_stars(year_stem_idx, year_branch_idx, lunar_month, shichen_idx):
    """보조성(길성·살성) 배치. branch_idx → {"吉": [...], "煞": [...]}"""
    aux = {}

    def add(branch, star, kind):
        aux.setdefault(branch, {"吉": [], "煞": []})
        aux[branch][kind].append(star)

    # 左輔 (월 기준, 辰에서 순행)
    zuofu = (3 + lunar_month) % 12
    add(zuofu, "左輔", "吉")

    # 右弼 (월 기준, 戌에서 역행)
    youbi = (11 - lunar_month) % 12
    add(youbi, "右弼", "吉")

    # 文昌 (시 기준, 戌에서 역행)
    wenchang = (10 - shichen_idx) % 12
    add(wenchang, "文昌", "吉")

    # 文曲 (시 기준, 辰에서 순행)
    wenqu = (4 + shichen_idx) % 12
    add(wenqu, "文曲", "吉")

    # 天魁·天鉞 (年干)
    add(TIANKUI[year_stem_idx], "天魁", "吉")
    add(TIANYUE[year_stem_idx], "天鉞", "吉")

    # 祿存 (年干)
    lucun_br = LUCUN[year_stem_idx]
    add(lucun_br, "祿存", "吉")

    # 擎羊 (祿存+1)
    add((lucun_br + 1) % 12, "擎羊", "煞")

    # 陀羅 (祿存-1)
    add((lucun_br - 1) % 12, "陀羅", "煞")

    # 火星 (年支그룹 + 시진)
    group = BRANCH_GROUP[year_branch_idx]
    huoxing = (HUOXING_START[group] + shichen_idx) % 12
    add(huoxing, "火星", "煞")

    # 鈴星 (年支그룹 + 시진)
    lingxing = (LINGXING_START[group] + shichen_idx) % 12
    add(lingxing, "鈴星", "煞")

    # 地空 (시진, 亥에서 역행)
    dikong = (11 - shichen_idx) % 12
    add(dikong, "地空", "煞")

    # 地劫 (시진, 亥에서 순행)
    dijie = (11 + shichen_idx) % 12
    add(dijie, "地劫", "煞")

    # 天馬 (年支)
    tianma_br = TIANMA[year_branch_idx]
    add(tianma_br, "天馬", "吉")

    return aux


# ═══════════════════════════════════════════════════
#  사화 배치
# ═══════════════════════════════════════════════════

def place_sihua(year_stem_idx, star_positions):
    """
    生年四化 배치.
    star_positions: {star_name: branch_idx, ...}
    Returns: {branch_idx: [(star_name, sihua_name), ...], ...}
    """
    sihua_stars = SIHUA[year_stem_idx]
    result = {}
    for i, star_name in enumerate(sihua_stars):
        sihua_name = SIHUA_NAMES[i]
        # 보조성(文昌, 文曲, 左輔, 右弼)은 main star positions에 없을 수 있음
        if star_name in star_positions:
            br = star_positions[star_name]
            result.setdefault(br, []).append((star_name, sihua_name))
    return result


# ═══════════════════════════════════════════════════
#  대한 계산
# ═══════════════════════════════════════════════════

def calc_dahan(mingong_branch, bureau, is_forward):
    """
    대한 배열 계산.
    is_forward: True=순행(양년남/음년여), False=역행(음년남/양년여)
    Returns: [(start_age, end_age, branch_idx), ...]
    """
    result = []
    start_age = bureau
    direction = 1 if is_forward else -1
    for i in range(12):
        br = (mingong_branch + direction * i) % 12
        end_age = start_age + 9
        result.append((start_age, end_age, br))
        start_age = end_age + 1
    return result


# ═══════════════════════════════════════════════════
#  전체 명반 계산
# ═══════════════════════════════════════════════════

def calculate_chart(lunar_year, lunar_month, lunar_day, hour, minute, gender):
    """
    전체 자미두수 명반을 계산한다.
    gender: 'M' 또는 'F'
    """
    # 年干·年支
    year_stem_idx = (lunar_year - 4) % 10
    year_branch_idx = (lunar_year - 4) % 12

    # 시진
    shichen_idx = hour_to_shichen(hour, minute)
    shichen_boundary = is_shichen_boundary(hour, minute)

    # 명궁·신궁
    mingong_branch = calc_mingong(lunar_month, shichen_idx)
    shengong_branch = calc_shengong(lunar_month, shichen_idx)

    # 명궁 천간
    mingong_stem = palace_stem(year_stem_idx, mingong_branch)

    # 오행국
    bureau, nayin_name, nayin_element = nayin_bureau(mingong_stem, mingong_branch)

    # 紫微 위치
    ziwei_branch = calc_ziwei_branch(lunar_day, bureau)

    # 주성 배치
    main_stars = place_main_stars(ziwei_branch)

    # star_name → branch_idx 매핑 (사화 계산용)
    star_positions = {}
    for br, stars in main_stars.items():
        for s in stars:
            star_positions[s] = br

    # 보조성 배치
    aux_stars = place_auxiliary_stars(
        year_stem_idx, year_branch_idx, lunar_month, shichen_idx
    )

    # 보조성도 star_positions에 추가 (사화가 보조성에 걸릴 수 있음)
    for br, kinds in aux_stars.items():
        for star in kinds["吉"] + kinds["煞"]:
            if star not in star_positions:
                star_positions[star] = br

    # 사화 배치
    sihua = place_sihua(year_stem_idx, star_positions)

    # 대한
    is_yang_year = year_stem_idx % 2 == 0
    is_male = gender.upper() == 'M'
    is_forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)
    dahan = calc_dahan(mingong_branch, bureau, is_forward)

    # 12궁 데이터 조립
    palaces = []
    for palace_idx in range(12):
        br = (mingong_branch - palace_idx) % 12
        p_stem = palace_stem(year_stem_idx, br)
        p_stars = main_stars.get(br, [])
        p_aux = aux_stars.get(br, {"吉": [], "煞": []})
        p_sihua = sihua.get(br, [])

        # 밝기
        brightness = {}
        for s in p_stars:
            brightness[s] = BRIGHTNESS.get(s, [""] * 12)[br]

        palaces.append({
            "index": palace_idx,
            "name": PALACE_NAMES[palace_idx],
            "name_kr": PALACE_NAMES_KR[palace_idx],
            "branch": br,
            "stem": p_stem,
            "main_stars": p_stars,
            "brightness": brightness,
            "ji_stars": p_aux["吉"],
            "sha_stars": p_aux["煞"],
            "sihua": p_sihua,
            "is_shengong": br == shengong_branch,
        })

    # 사화 요약
    sihua_summary = []
    for i, star_name in enumerate(SIHUA[year_stem_idx]):
        if star_name in star_positions:
            br = star_positions[star_name]
            # 해당 궁 이름 찾기
            palace_name = ""
            for p in palaces:
                if p["branch"] == br:
                    palace_name = p["name"]
                    break
            sihua_summary.append({
                "type": SIHUA_NAMES[i],
                "star": star_name,
                "branch": br,
                "palace": palace_name,
            })

    return {
        "lunar_year": lunar_year,
        "lunar_month": lunar_month,
        "lunar_day": lunar_day,
        "year_stem": year_stem_idx,
        "year_branch": year_branch_idx,
        "shichen": shichen_idx,
        "mingong_branch": mingong_branch,
        "mingong_stem": mingong_stem,
        "shengong_branch": shengong_branch,
        "bureau": bureau,
        "nayin_name": nayin_name,
        "nayin_element": nayin_element,
        "ziwei_branch": ziwei_branch,
        "palaces": palaces,
        "sihua_summary": sihua_summary,
        "dahan": dahan,
        "dahan_direction": "順行" if is_forward else "逆行",
        "gender": gender,
        "shichen_boundary": shichen_boundary,  # None 또는 (이전시진, 다음시진)
    }


# ═══════════════════════════════════════════════════
#  터미널 출력
# ═══════════════════════════════════════════════════

def print_chart(chart, name, solar_date_str=None):
    """터미널용 포맷 출력"""
    ys = chart["year_stem"]
    yb = chart["year_branch"]
    ms = chart["mingong_stem"]
    mb = chart["mingong_branch"]
    sb = chart["shengong_branch"]

    print("=" * 60)
    print("  紫微斗數 命盤")
    print(f"  이름: {name}")
    if solar_date_str:
        print(f"  양력: {solar_date_str}")
    print(f"  음력: {STEMS[ys]}{BRANCHES[yb]}年 "
          f"{chart['lunar_month']}月 {chart['lunar_day']}日 "
          f"{BRANCHES[chart['shichen']]}時")
    print(f"  성별: {'男' if chart['gender'] == 'M' else '女'}")
    print("=" * 60)

    # 시진 경계 경고
    if chart["shichen_boundary"]:
        prev_sh, next_sh = chart["shichen_boundary"]
        print()
        print("  ⚠ 시진 경계 시간!")
        print(f"    출생 시간이 {BRANCHES[prev_sh]}時/{BRANCHES[next_sh]}時 경계에 걸립니다.")
        print(f"    현재 {BRANCHES[chart['shichen']]}時로 계산했으나,")
        print(f"    {BRANCHES[prev_sh]}時일 가능성도 있습니다.")
        print(f"    → 양쪽 명반을 비교하여 본인에게 맞는 시진을 확인하세요.")

    print()

    # 기본 정보
    print("─" * 60)
    print("  ■ 기본 정보")
    print("─" * 60)
    print(f"  年柱: {STEMS[ys]}{BRANCHES[yb]}")
    print(f"  命宮: {STEMS[ms]}{BRANCHES[mb]}")

    # 신궁이 어느 궁에 해당하는지
    shengong_palace = ""
    for p in chart["palaces"]:
        if p["branch"] == sb:
            shengong_palace = p["name"]
            break
    print(f"  身宮: {shengong_palace} ({BRANCHES[sb]})")
    print(f"  五行局: {BUREAU_NAMES[chart['bureau']]} (납음: {chart['nayin_name']})")
    print(f"  大限起始: {chart['bureau']}歲 ({chart['dahan_direction']})")
    print()

    # 12궁 배치
    print("─" * 60)
    print("  ■ 12궁 배치")
    print("─" * 60)
    for p in chart["palaces"]:
        stem_ch = STEMS[p["stem"]]
        branch_ch = BRANCHES[p["branch"]]
        label = p["name"]
        if p["is_shengong"]:
            label += "·身"

        # 주성 + 밝기
        star_strs = []
        for s in p["main_stars"]:
            br_text = p["brightness"].get(s, "")
            star_strs.append(f"{s} {br_text}" if br_text else s)
        stars_line = ", ".join(star_strs) if star_strs else "(空宮)"

        # 사화
        sihua_strs = []
        for star, sh_name in p["sihua"]:
            sihua_strs.append(f"{sh_name}({star})")
        sihua_line = " ".join(sihua_strs)

        # 길성·살성
        ji_line = ", ".join(p["ji_stars"]) if p["ji_stars"] else ""
        sha_line = ", ".join(p["sha_stars"]) if p["sha_stars"] else ""

        print(f"  {label:<8} {stem_ch}{branch_ch}  {stars_line}")
        if ji_line:
            print(f"{'':>14}吉: {ji_line}")
        if sha_line:
            print(f"{'':>14}煞: {sha_line}")
        if sihua_line:
            print(f"{'':>14}四化: {sihua_line}")
        print()

    # 사화 요약
    print("─" * 60)
    print(f"  ■ 生年四化 ({STEMS[ys]}年)")
    print("─" * 60)
    for sh in chart["sihua_summary"]:
        print(f"  {sh['type']}: {sh['star']} → {sh['palace']}({BRANCHES[sh['branch']]})")
    print()

    # 대한
    print("─" * 60)
    print(f"  ■ 大限 ({chart['dahan_direction']})")
    print("─" * 60)
    for start_age, end_age, br in chart["dahan"]:
        # 이 대한 궁의 주성 찾기
        d_stars = []
        for p in chart["palaces"]:
            if p["branch"] == br:
                d_stars = p["main_stars"]
                break
        stars_str = ", ".join(d_stars) if d_stars else "(空宮)"

        # 궁 이름 찾기
        d_palace = ""
        for p in chart["palaces"]:
            if p["branch"] == br:
                d_palace = p["name"]
                break

        print(f"  {start_age:>3}-{end_age:<3}歲  {d_palace}({BRANCHES[br]})  {stars_str}")
    print()

    print("=" * 60)
    print("  ※ 자미두수는 음력 기준. 사주의 年柱(입춘 기준)와 다를 수 있음.")
    print("=" * 60)


# ═══════════════════════════════════════════════════
#  마크다운 출력 (contexts 파일용)
# ═══════════════════════════════════════════════════

def print_markdown(chart, name, solar_date_str=None):
    """contexts 파일에 붙여넣기 가능한 마크다운 형식 출력"""
    ys = chart["year_stem"]
    yb = chart["year_branch"]
    ms = chart["mingong_stem"]
    mb = chart["mingong_branch"]
    sb = chart["shengong_branch"]

    shengong_palace = ""
    for p in chart["palaces"]:
        if p["branch"] == sb:
            shengong_palace = p["name"]
            break

    print()
    print("# 자미두수 (紫微斗數)")
    print()
    print("## 기본 정보")
    print()
    print(f"- **음력 생년월일시**: {STEMS[ys]}{BRANCHES[yb]}年 "
          f"{chart['lunar_month']}月 {chart['lunar_day']}日 "
          f"{BRANCHES[chart['shichen']]}時")
    print(f"- **오행국(五行局)**: {BUREAU_NAMES[chart['bureau']]} (납음: {chart['nayin_name']})")
    print(f"- **명궁(命宮) 위치**: {BRANCHES[mb]} (천간: {STEMS[ms]})")
    print(f"- **신궁(身宮) 위치**: {BRANCHES[sb]} — {shengong_palace}에 동궁")
    if chart["shichen_boundary"]:
        prev_sh, next_sh = chart["shichen_boundary"]
        print(f"- **⚠ 시진 경계**: 출생 시간이 "
              f"{BRANCHES[prev_sh]}時/{BRANCHES[next_sh]}時 경계 — "
              f"{BRANCHES[chart['shichen']]}時로 계산, 반대쪽 명반 비교 필요")
    print(f"- **대한 방향**: {chart['dahan_direction']}")
    print(f"- **대한 기시**: {chart['bureau']}세")
    print()

    # 12궁 배치
    print("## 12궁 배치")
    print()
    print("| 궁위 | 천간지지 | 주성(主星) | 밝기 | 보성(吉星) | 살성(煞星) | 사화(四化) |")
    print("|------|---------|-----------|------|-----------|-----------|-----------|")

    for p in chart["palaces"]:
        stem_ch = STEMS[p["stem"]]
        branch_ch = BRANCHES[p["branch"]]
        label = p["name"]
        if p["is_shengong"]:
            label += "·身"

        # 주성
        star_strs = []
        bright_strs = []
        for s in p["main_stars"]:
            star_strs.append(s)
            br_text = p["brightness"].get(s, "")
            bright_strs.append(br_text)

        stars_cell = ", ".join(star_strs) if star_strs else "(空宮)"
        bright_cell = ", ".join(bright_strs) if bright_strs else ""

        ji_cell = ", ".join(p["ji_stars"]) if p["ji_stars"] else ""
        sha_cell = ", ".join(p["sha_stars"]) if p["sha_stars"] else ""

        sihua_strs = []
        for star, sh_name in p["sihua"]:
            sihua_strs.append(sh_name)
        sihua_cell = ", ".join(sihua_strs) if sihua_strs else ""

        print(f"| {label} | {stem_ch}{branch_ch} | {stars_cell} | {bright_cell} "
              f"| {ji_cell} | {sha_cell} | {sihua_cell} |")

    print()

    # 사화
    print("## 생년사화(生年四化)")
    print()
    for sh in chart["sihua_summary"]:
        print(f"- **{sh['type']}**: {sh['star']} → {sh['palace']}({BRANCHES[sh['branch']]})")
    print()

    # 대한
    print("## 대한(大限) 배열")
    print()
    print("| 순서 | 나이 | 대한 궁위 | 지지 | 주성 |")
    print("|------|------|----------|------|------|")

    for i, (start_age, end_age, br) in enumerate(chart["dahan"]):
        d_stars = []
        d_palace = ""
        for p in chart["palaces"]:
            if p["branch"] == br:
                d_stars = p["main_stars"]
                d_palace = p["name"]
                break
        stars_str = ", ".join(d_stars) if d_stars else "(空宮)"
        print(f"| {i+1} | {start_age}-{end_age}세 | {d_palace} | {BRANCHES[br]} | {stars_str} |")

    print()
    print("## 특이사항")
    print()
    print("- **기타 메모**:")


# ═══════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="자미두수(紫微斗數) 명반 생성기"
    )
    parser.add_argument("--name", type=str, required=True, help="이름")
    parser.add_argument("--date", type=str, required=True,
                        help="생년월일 (YYYY-MM-DD)")
    parser.add_argument("--time", type=str, required=True,
                        help="출생 시간 (HH:MM, KST)")
    parser.add_argument("--gender", type=str, required=True,
                        choices=["M", "F", "m", "f"],
                        help="성별 (M: 남, F: 여)")
    parser.add_argument("--lunar", action="store_true",
                        help="날짜를 음력으로 입력 (기본: 양력)")
    parser.add_argument("--markdown", action="store_true",
                        help="마크다운 형식으로 출력 (contexts 파일용)")
    return parser.parse_args()


def main():
    args = parse_args()

    # 날짜 파싱
    dt = datetime.strptime(args.date, "%Y-%m-%d")
    year, month, day = dt.year, dt.month, dt.day

    # 시간 파싱
    time_parts = args.time.split(":")
    hour = int(time_parts[0])
    minute = int(time_parts[1]) if len(time_parts) > 1 else 0

    # 음력 변환
    solar_date_str = args.date
    if args.lunar:
        lunar_year, lunar_month, lunar_day = year, month, day
        solar_date_str = None
    else:
        ld = LunarDate.fromSolarDate(year, month, day)
        lunar_year = ld.year
        lunar_month = ld.month
        lunar_day = ld.day

    # 명반 계산
    chart = calculate_chart(
        lunar_year, lunar_month, lunar_day,
        hour, minute, args.gender.upper()
    )

    # 출력
    if args.markdown:
        print_markdown(chart, args.name, solar_date_str)
    else:
        print_chart(chart, args.name, solar_date_str)


if __name__ == "__main__":
    main()
