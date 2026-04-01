#!/usr/bin/env python3
"""
saju_generator.py - 생년월일시만으로 만세력 데이터 자동 생성

사용법:
    python3 saju_generator.py --name 홍길동 --date 1990-05-15 --time 14:30 --gender 남
    python3 saju_generator.py --name 홍길동 --date 1990-05-15 --time 14:30 --gender 남 --save
"""

import sys
import argparse
import math
from datetime import date, datetime, timedelta
from pathlib import Path

from saju_calendar import (
    CHEONGAN, CHEONGAN_HANJA, JIJI, JIJI_HANJA,
    OHAENG, JIJI_OHAENG, TWELVE_ANIMALS,
    get_year_ganji, get_month_ganji, get_day_ganji,
    julian_day_number, get_saju_month,
)

# ─── 음양 ───

UMYANG = {
    "갑": "양", "을": "음", "병": "양", "정": "음", "무": "양",
    "기": "음", "경": "양", "신": "음", "임": "양", "계": "음",
}

# ─── 시간 → 지지 매핑 ───

def hour_to_branch_idx(hour: int) -> int:
    """시간(0~23) → 지지 인덱스 (자=0, 축=1, ...)"""
    if hour == 23:
        return 0  # 야자시
    return ((hour + 1) // 2) % 12


# ─── 시주 계산 ───

def get_time_pillar(day_stem: str, hour: int, minute: int = 0) -> tuple[str, str]:
    """일간 + 출생시간으로 시주(시간천간, 시간지지) 계산"""
    branch_idx = hour_to_branch_idx(hour)
    day_stem_idx = CHEONGAN.index(day_stem)

    # 일간별 자시 시작 천간: 갑기→갑(0), 을경→병(2), 병신→무(4), 정임→경(6), 무계→임(8)
    base = (day_stem_idx % 5) * 2
    stem_idx = (base + branch_idx) % 10

    return CHEONGAN[stem_idx], JIJI[branch_idx]


# ─── 사주 원국 (야자시 처리 포함) ───

def get_four_pillars(year: int, month: int, day: int, hour: int, minute: int = 0):
    """사주 사주 전체 계산. 야자시(23시) 처리 포함."""
    # 야자시: 일주는 다음날 기준
    if hour >= 23:
        next_day = date(year, month, day) + timedelta(days=1)
        day_y, day_m, day_d = next_day.year, next_day.month, next_day.day
    else:
        day_y, day_m, day_d = year, month, day

    year_stem, year_branch = get_year_ganji(year, month, day)
    month_stem, month_branch = get_month_ganji(year, month, day)
    day_stem, day_branch = get_day_ganji(day_y, day_m, day_d)
    time_stem, time_branch = get_time_pillar(day_stem, hour, minute)

    return {
        "year": (year_stem, year_branch),
        "month": (month_stem, month_branch),
        "day": (day_stem, day_branch),
        "time": (time_stem, time_branch),
    }


# ─── 60갑자 인덱스 ───

def ganji_cycle_index(stem: str, branch: str) -> int:
    """간지의 60갑자 순서 인덱스 (0~59)"""
    si = CHEONGAN.index(stem)
    bi = JIJI.index(branch)
    for n in range(60):
        if n % 10 == si and n % 12 == bi:
            return n
    return -1


def cycle_index_to_ganji(idx: int) -> tuple[str, str]:
    """60갑자 인덱스 → 간지"""
    return CHEONGAN[idx % 10], JIJI[idx % 12]


# ─── 십성 (十星) ───

SANGSAENG = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
SANGGEUK = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}


def get_sipsung(day_stem: str, target_stem: str) -> str:
    """일간 기준으로 대상 천간의 십성을 구한다."""
    if day_stem == target_stem:
        return "비견"

    day_oh = OHAENG[day_stem]
    tgt_oh = OHAENG[target_stem]
    same_yy = (UMYANG[day_stem] == UMYANG[target_stem])

    if day_oh == tgt_oh:
        return "비견" if same_yy else "겁재"
    elif SANGSAENG[day_oh] == tgt_oh:  # 내가 생
        return "식신" if same_yy else "상관"
    elif SANGSAENG[tgt_oh] == day_oh:  # 나를 생
        return "편인" if same_yy else "정인"
    elif SANGGEUK[day_oh] == tgt_oh:  # 내가 극
        return "편재" if same_yy else "정재"
    elif SANGGEUK[tgt_oh] == day_oh:  # 나를 극
        return "편관" if same_yy else "정관"
    return "?"


# ─── 지장간 ───

JIJANGGAN = {
    "자": "임계",    "축": "계신기",   "인": "무병갑",   "묘": "갑을",
    "진": "을계무",  "사": "무경병",   "오": "병기정",   "미": "정을기",
    "신": "무임경",  "유": "경신",     "술": "신정무",   "해": "무갑임",
}

JIJANGGAN_HANJA = {
    "자": "壬癸",     "축": "癸辛己",   "인": "戊丙甲",   "묘": "甲乙",
    "진": "乙癸戊",   "사": "戊庚丙",   "오": "丙己丁",   "미": "丁乙己",
    "신": "戊壬庚",   "유": "庚辛",     "술": "辛丁戊",   "해": "戊甲壬",
}

# 본기 (각 지지의 주된 오행을 나타내는 천간) = 지장간의 마지막 글자
BONGI = {
    "자": "계", "축": "기", "인": "갑", "묘": "을",
    "진": "무", "사": "병", "오": "정", "미": "기",
    "신": "경", "유": "신", "술": "무", "해": "임",
}


def get_jiji_sipsung(day_stem: str, branch: str) -> str:
    """지지의 본기 기준 십성"""
    return get_sipsung(day_stem, BONGI[branch])


# ─── 12운성 ───

TWELVE_STAGES = ["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"]

STAGE_START = {
    "갑": 11, "을": 6, "병": 2, "정": 9, "무": 2,
    "기": 9,  "경": 5, "신": 0, "임": 8, "계": 3,
}


def get_twelve_stage(stem: str, branch: str) -> str:
    """천간의 지지에서의 12운성"""
    si = CHEONGAN.index(stem)
    bi = JIJI.index(branch)
    start = STAGE_START[stem]

    if UMYANG[stem] == "양":
        idx = (bi - start) % 12
    else:
        idx = (start - bi) % 12

    return TWELVE_STAGES[idx]


# ─── 납음 ───

NAPEUM = [
    "해중금", "노중화", "대림목", "노방토", "검봉금", "산두화",
    "간하수", "성두토", "백납금", "양류목", "천중수", "옥상토",
    "벽력화", "송백목", "장류수", "사중금", "산하화", "평지목",
    "벽상토", "금박금", "복등화", "천하수", "대역토", "차천금",
    "상자목", "대계수", "사중토", "천상화", "석류목", "대해수",
]


def get_napeum(stem: str, branch: str) -> str:
    """간지의 납음"""
    idx = ganji_cycle_index(stem, branch)
    return NAPEUM[idx // 2]


# ─── 공망 ───

GONGMANG_TABLE = [
    ("술", "해"),  # 甲子旬 (0~9)
    ("신", "유"),  # 甲戌旬 (10~19)
    ("오", "미"),  # 甲申旬 (20~29)
    ("진", "사"),  # 甲午旬 (30~39)
    ("인", "묘"),  # 甲辰旬 (40~49)
    ("자", "축"),  # 甲寅旬 (50~59)
]


def get_gongmang(stem: str, branch: str) -> tuple[str, str]:
    """간지의 공망 지지 2개 반환"""
    idx = ganji_cycle_index(stem, branch)
    return GONGMANG_TABLE[idx // 10]


def gongmang_hanja(gm: tuple[str, str]) -> str:
    """공망 지지를 한자로"""
    h1 = JIJI_HANJA[JIJI.index(gm[0])]
    h2 = JIJI_HANJA[JIJI.index(gm[1])]
    return f"{h1}{h2}"


# ─── 오행 분포 ───

def calc_ohaeng(pillars: dict) -> dict:
    """사주 8자의 오행 개수"""
    count = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for stem, branch in pillars.values():
        count[OHAENG[stem]] += 1
        count[JIJI_OHAENG[branch]] += 1
    return count


# ─── 합충형파해 ───

YUKHAP = [(0, 1), (2, 11), (3, 10), (4, 9), (5, 8), (6, 7)]  # 자축, 인해, 묘술, 진유, 사신, 오미
SAMHAP_GROUPS = [
    (8, 0, 4, "수국"),   # 申子辰
    (11, 3, 7, "목국"),  # 亥卯未
    (2, 6, 10, "화국"),  # 寅午戌
    (5, 9, 1, "금국"),   # 巳酉丑
]
BANGHAP_GROUPS = [
    (2, 3, 4, "목"),   # 寅卯辰
    (5, 6, 7, "화"),   # 巳午未
    (8, 9, 10, "금"),  # 申酉戌
    (11, 0, 1, "수"),  # 亥子丑
]
CHUNG = [(0, 6), (1, 7), (2, 8), (3, 9), (4, 10), (5, 11)]  # 자오, 축미, 인신, 묘유, 진술, 사해
HYUNG_PAIRS = [(2, 5), (5, 8), (2, 8), (1, 10), (10, 7), (1, 7), (0, 3)]
JAHYUNG = [4, 6, 9, 11]  # 진진, 오오, 유유, 해해
PA_PAIRS = [(0, 9), (3, 6), (2, 11), (5, 8), (4, 1), (10, 7)]
HAE_PAIRS = [(0, 7), (1, 6), (2, 5), (3, 4), (8, 11), (9, 10)]
WONJIN = [(0, 7), (1, 6), (2, 9), (3, 8), (4, 11), (5, 10)]

PILLAR_NAMES = ["년", "월", "일", "시"]


def _check_pair(bi1, bi2, table):
    for a, b in table:
        if (bi1 == a and bi2 == b) or (bi1 == b and bi2 == a):
            return True
    return False


def calc_hapchung(pillars: dict) -> list[str]:
    """사주 지지 간 합충형파해 관계 분석"""
    keys = ["year", "month", "day", "time"]
    names = ["년", "월", "일", "시"]
    branches = [JIJI.index(pillars[k][1]) for k in keys]
    results = []

    for i in range(4):
        for j in range(i + 1, 4):
            bi, bj = branches[i], branches[j]
            bh_i = JIJI_HANJA[bi]
            bh_j = JIJI_HANJA[bj]
            pair_label = f"{names[i]}지({bh_i})-{names[j]}지({bh_j})"

            if _check_pair(bi, bj, YUKHAP):
                results.append(f"{pair_label} 육합(六合)")
            if _check_pair(bi, bj, CHUNG):
                results.append(f"{pair_label} 충(沖)")
            if _check_pair(bi, bj, HYUNG_PAIRS):
                results.append(f"{pair_label} 형(刑)")
            if bi == bj and bi in JAHYUNG:
                results.append(f"{pair_label} 자형(自刑)")
            if bi == bj and bi not in JAHYUNG:
                results.append(f"{pair_label} 같은 지지")
            if _check_pair(bi, bj, PA_PAIRS):
                results.append(f"{pair_label} 파(破)")
            if _check_pair(bi, bj, HAE_PAIRS):
                results.append(f"{pair_label} 해(害)")
            if _check_pair(bi, bj, WONJIN):
                results.append(f"{pair_label} 원진(怨嗔)")

    # 삼합 체크
    for g1, g2, g3, name in SAMHAP_GROUPS:
        found = [i for i, b in enumerate(branches) if b in (g1, g2, g3)]
        matched = {branches[i] for i in found}
        if len(matched & {g1, g2, g3}) >= 2:
            positions = "+".join(names[i] for i in found)
            matched_hanja = "".join(JIJI_HANJA[b] for b in sorted(matched & {g1, g2, g3}))
            if len(matched & {g1, g2, g3}) == 3:
                results.append(f"{matched_hanja} 삼합({name}) [{positions}]")
            else:
                results.append(f"{matched_hanja} 반합({name}) [{positions}]")

    # 방합 체크
    for g1, g2, g3, name in BANGHAP_GROUPS:
        found = [i for i, b in enumerate(branches) if b in (g1, g2, g3)]
        matched = {branches[i] for i in found}
        if len(matched & {g1, g2, g3}) >= 2:
            positions = "+".join(names[i] for i in found)
            matched_hanja = "".join(JIJI_HANJA[b] for b in sorted(matched & {g1, g2, g3}))
            results.append(f"{matched_hanja} 방합({name}) [{positions}]")

    return results


# ─── 천간 합충 ───

CHEONGAN_HAP = [(0, 5), (1, 6), (2, 7), (3, 8), (4, 9)]  # 갑기, 을경, 병신, 정임, 무계
CHEONGAN_CHUNG = [(0, 6), (1, 7), (2, 8), (3, 9), (4, 5)]  # 갑경 극... 실제로 천간충은 7칸 차이


def calc_cheongan_hapchung(pillars: dict) -> list[str]:
    """천간 합/충 관계"""
    keys = ["year", "month", "day", "time"]
    names = ["년", "월", "일", "시"]
    stems = [CHEONGAN.index(pillars[k][0]) for k in keys]
    results = []

    for i in range(4):
        for j in range(i + 1, 4):
            si, sj = stems[i], stems[j]
            sh_i = CHEONGAN_HANJA[si]
            sh_j = CHEONGAN_HANJA[sj]
            pair_label = f"{names[i]}간({sh_i})-{names[j]}간({sh_j})"
            for a, b in CHEONGAN_HAP:
                if (si == a and sj == b) or (si == b and sj == a):
                    results.append(f"{pair_label} 간합(干合)")
    return results


# ─── 신살 ───

SHINSAL_12 = ["겁살", "재살", "천살", "지살", "년살", "월살", "망신살", "장성살", "반안살", "역마살", "육해살", "화개살"]

SAMHAP_MEMBER = {}
for g1, g2, g3, name in SAMHAP_GROUPS:
    for g in (g1, g2, g3):
        SAMHAP_MEMBER[g] = (g1, g2, g3, name)

# 겁살 시작 지지 (각 삼합국별 겁살 위치)
GEOBSAL_START = {
    "수국": 5,   # 巳
    "목국": 8,   # 申
    "화국": 11,  # 亥
    "금국": 2,   # 寅
}


def calc_12shinsal(ref_branch: str, target_branch: str) -> list[str]:
    """기준 지지(년지 또는 일지)로 대상 지지의 12신살"""
    ref_idx = JIJI.index(ref_branch)
    tgt_idx = JIJI.index(target_branch)

    _, _, _, group_name = SAMHAP_MEMBER[ref_idx]
    start = GEOBSAL_START[group_name]

    offset = (tgt_idx - start) % 12
    return [SHINSAL_12[offset]]


def calc_shinsal_all(pillars: dict) -> dict:
    """년지/일지 기준 모든 주의 12신살"""
    keys = ["year", "month", "day", "time"]
    year_branch = pillars["year"][1]
    day_branch = pillars["day"][1]
    result = {}

    for i, k in enumerate(keys):
        branch = pillars[k][1]
        shinsals = set()
        # 년지 기준
        for s in calc_12shinsal(year_branch, branch):
            shinsals.add(s)
        # 일지 기준
        for s in calc_12shinsal(day_branch, branch):
            shinsals.add(s)
        result[PILLAR_NAMES[i]] = sorted(shinsals)

    return result


# ─── 천을귀인 ───

CHEONEUL_GUIIN = {
    "갑": ["축", "미"], "무": ["축", "미"],
    "을": ["자", "신"], "기": ["자", "신"],
    "병": ["해", "유"], "정": ["해", "유"],
    "경": ["오", "인"], "신": ["오", "인"],
    "임": ["묘", "사"], "계": ["묘", "사"],
}


# ─── 대운 계산 ───

# 절기 경계 (양력 월, 일) — 근사값
JEOLGI_BOUNDARIES = [
    (1, 6),   # 소한
    (2, 4),   # 입춘
    (3, 6),   # 경칩
    (4, 5),   # 청명
    (5, 6),   # 입하
    (6, 6),   # 망종
    (7, 7),   # 소서
    (8, 7),   # 입추
    (9, 8),   # 백로
    (10, 8),  # 한로
    (11, 7),  # 입동
    (12, 7),  # 대설
]


def _jeolgi_dates_for_year(year: int) -> list[date]:
    """주어진 연도의 절기 날짜 리스트 (오름차순)"""
    dates = []
    for m, d in JEOLGI_BOUNDARIES:
        dates.append(date(year, m, d))
    return sorted(dates)


def calc_daewoon_start_age(birth: date, direction: str) -> int:
    """대운 시작 나이 계산 (근사값)"""
    # 현재 연도 ± 1년 범위의 절기 날짜 모음
    all_jeolgi = []
    for y in range(birth.year - 1, birth.year + 2):
        all_jeolgi.extend(_jeolgi_dates_for_year(y))
    all_jeolgi.sort()

    if direction == "순행":
        # 생일 이후 가장 가까운 절기
        target = None
        for jd in all_jeolgi:
            if jd > birth:
                target = jd
                break
        if target is None:
            return 1
        diff = (target - birth).days
    else:
        # 생일 이전 가장 가까운 절기
        target = None
        for jd in reversed(all_jeolgi):
            if jd <= birth:
                target = jd
                break
        if target is None:
            return 1
        diff = (birth - target).days

    age = round(diff / 3)
    return max(age, 1)


def calc_daewoon(pillars: dict, gender: str, birth_year: int, birth_month: int, birth_day: int) -> dict:
    """대운 배열 계산"""
    year_stem = pillars["year"][0]
    month_stem = pillars["month"][0]
    month_branch = pillars["month"][1]
    day_stem = pillars["day"][0]

    # 순행/역행 결정
    is_yang = (UMYANG[year_stem] == "양")
    is_male = (gender == "남")
    direction = "순행" if (is_yang == is_male) else "역행"

    # 시작 나이
    birth = date(birth_year, birth_month, birth_day)
    start_age = calc_daewoon_start_age(birth, direction)

    # 대운 배열 생성
    month_cycle = ganji_cycle_index(month_stem, month_branch)
    daewoons = []

    for i in range(1, 12):
        if direction == "순행":
            idx = (month_cycle + i) % 60
        else:
            idx = (month_cycle - i) % 60

        dw_stem, dw_branch = cycle_index_to_ganji(idx)
        age = start_age + (i - 1) * 10
        start_year_val = birth_year + age - 1  # 전통 나이 기준

        daewoons.append({
            "order": i,
            "age": age,
            "stem": dw_stem,
            "branch": dw_branch,
            "start_year": start_year_val,
            "cheongan_sipsung": get_sipsung(day_stem, dw_stem),
            "jiji_sipsung": get_jiji_sipsung(day_stem, dw_branch),
        })

    return {
        "direction": direction,
        "start_age": start_age,
        "list": daewoons,
    }


# ─── 한자 변환 유틸 ───

def hanja(stem: str, branch: str) -> str:
    return CHEONGAN_HANJA[CHEONGAN.index(stem)] + JIJI_HANJA[JIJI.index(branch)]


def stem_hanja(stem: str) -> str:
    return CHEONGAN_HANJA[CHEONGAN.index(stem)]


def branch_hanja(branch: str) -> str:
    return JIJI_HANJA[JIJI.index(branch)]


# ─── 마크다운 출력 ───

def generate_markdown(
    name: str, gender: str,
    birth_year: int, birth_month: int, birth_day: int,
    hour: int, minute: int,
    pillars: dict, daewoon: dict,
) -> str:
    """전체 만세력 데이터를 마크다운으로 출력"""
    day_stem = pillars["day"][0]
    day_oh = OHAENG[day_stem]
    day_yy = UMYANG[day_stem]

    # 기본 정보
    lines = [
        "# 사주 정보",
        "",
        "## 기본 정보",
        "",
        f"- **이름**: {name}",
        f"- **성별**: {gender}",
        f"- **생년월일**: 양력 {birth_year:04d}-{birth_month:02d}-{birth_day:02d}",
        f"- **태어난 시간**: {hour:02d}:{minute:02d}",
        "- **태어난 곳**: (미상)",
        "",
    ]

    # 사주 원국 테이블
    keys = ["year", "month", "day", "time"]
    col_names = ["년주(年柱)", "월주(月柱)", "일주(日柱)", "시주(時柱)"]

    def _col(key):
        s, b = pillars[key]
        return s, b

    stems = [pillars[k][0] for k in keys]
    branches = [pillars[k][1] for k in keys]

    stem_cells = [f"{stem_hanja(s)}({s})" for s in stems]
    branch_cells = [f"{branch_hanja(b)}({b})" for b in branches]
    sipsung_cheongan = ["일간" if i == 2 else get_sipsung(day_stem, stems[i]) for i in range(4)]
    sipsung_jiji = [get_jiji_sipsung(day_stem, b) for b in branches]
    jijanggan_cells = [JIJANGGAN_HANJA[b] for b in branches]

    # 12운성: 일간기준(해당주천간기준)
    stage_cells = []
    for i in range(4):
        s1 = get_twelve_stage(day_stem, branches[i])
        s2 = get_twelve_stage(stems[i], branches[i])
        stage_cells.append(f"{s1}({s2})")

    napeum_cells = [get_napeum(stems[i], branches[i]) for i in range(4)]

    lines += [
        "## 사주 원국 (四柱八字)",
        "",
        f"|        | {' | '.join(col_names)} |",
        "|--------|-----------|-----------|-----------|-----------|",
        f"| 천간   | {' | '.join(f'{c:9s}' for c in stem_cells)} |",
        f"| 지지   | {' | '.join(f'{c:9s}' for c in branch_cells)} |",
        f"| 십성(천간) | {' | '.join(f'{c:9s}' for c in sipsung_cheongan)} |",
        f"| 십성(지지) | {' | '.join(f'{c:9s}' for c in sipsung_jiji)} |",
        f"| 지장간 | {' | '.join(f'{c:9s}' for c in jijanggan_cells)} |",
        f"| 12운성 | {' | '.join(f'{c:9s}' for c in stage_cells)} |",
        f"| 납음   | {' | '.join(f'{c:9s}' for c in napeum_cells)} |",
        "",
        f"- **일간(日干)**: {stem_hanja(day_stem)}({day_stem}) → 오행: {day_oh}({'木火土金水'['목화토금수'.index(day_oh)]}), {day_yy}{day_oh}({day_yy.replace('양','陽').replace('음','陰')}{day_oh.replace('목','木').replace('화','火').replace('토','土').replace('금','金').replace('수','水')})",
        f"- **음양**: {day_yy}({'陽' if day_yy == '양' else '陰'})",
        "",
    ]

    # 오행 분포
    ohaeng = calc_ohaeng(pillars)
    oh_names = ["목", "화", "토", "금", "수"]
    oh_hanja_map = {"목": "木", "화": "火", "토": "土", "금": "金", "수": "水"}

    strong = [f"{oh}({oh_hanja_map[oh]}) {ohaeng[oh]}개" for oh in oh_names if ohaeng[oh] == max(ohaeng.values())]
    weak = [f"{oh}({oh_hanja_map[oh]}) {ohaeng[oh]}개" for oh in oh_names if ohaeng[oh] == 0]
    if not weak:
        weak = [f"{oh}({oh_hanja_map[oh]}) {ohaeng[oh]}개" for oh in oh_names if ohaeng[oh] == min(ohaeng.values())]

    lines += [
        "## 오행 분포",
        "",
        f"| 오행 | 목(木) | 화(火) | 토(土) | 금(金) | 수(水) |",
        f"|------|--------|--------|--------|--------|--------|",
        f"| 개수 | {ohaeng['목']:6d} | {ohaeng['화']:6d} | {ohaeng['토']:6d} | {ohaeng['금']:6d} | {ohaeng['수']:6d} |",
        "",
        f"- **강한 오행**: {', '.join(strong)}",
        f"- **약한 오행**: {', '.join(weak)}" + (" — 완전 결핍" if any(ohaeng[oh] == 0 for oh in oh_names) else ""),
        "",
    ]

    # 용신 (분석 시 판단)
    lines += [
        "## 용신·희신·기신",
        "",
        "- **용신(用神)**: (분석 시 판단)",
        "- **희신(喜神)**: (분석 시 판단)",
        "- **기신(忌神)**: (분석 시 판단)",
        "- **한신(閑神)**: (분석 시 판단)",
        "- **구신(仇神)**: (분석 시 판단)",
        "",
    ]

    # 대운
    dw = daewoon
    lines += [
        "## 대운 (大運)",
        "",
        f"대운 시작 나이: {dw['start_age']}세 ({dw['direction']})",
        "",
        "| 순서 | 나이(전통) | 대운 간지    | 시작 년도 | 천간십성 | 지지십성 |",
        "|------|-----------|-------------|----------|---------|---------|",
    ]
    for d in dw["list"]:
        h = hanja(d["stem"], d["branch"])
        lines.append(
            f"| {d['order']:4d} | {d['age']}세{' ' * (7 - len(str(d['age'])))} | "
            f"{h}({d['stem']}{d['branch']}){' ' * (5 - len(d['stem'] + d['branch']))} | "
            f"{d['start_year']:8d} | {d['cheongan_sipsung']:7s} | {d['jiji_sipsung']:7s} |"
        )
    lines.append("")

    # 합충형파해
    hc_jiji = calc_hapchung(pillars)
    hc_cheongan = calc_cheongan_hapchung(pillars)

    lines += [
        "## 합충형파해",
        "",
    ]
    if hc_cheongan:
        for item in hc_cheongan:
            lines.append(f"- {item}")
    if hc_jiji:
        for item in hc_jiji:
            lines.append(f"- {item}")
    if not hc_cheongan and not hc_jiji:
        lines.append("- (특이 관계 없음)")
    lines.append("")

    # 특이사항
    gm_year = get_gongmang(pillars["year"][0], pillars["year"][1])
    gm_day = get_gongmang(pillars["day"][0], pillars["day"][1])
    guiin = CHEONEUL_GUIIN[day_stem]
    guiin_hanja_str = "".join(branch_hanja(g) for g in guiin)

    lines += [
        "## 특이사항",
        "",
        f"- **공망(空亡)**: [年] {gongmang_hanja(gm_year)}, [日] {gongmang_hanja(gm_day)}",
        f"- **천을귀인**: {guiin_hanja_str}",
    ]

    # 공망에 해당하는 주 표시
    gm_year_set = set(gm_year)
    gm_day_set = set(gm_day)
    for i, k in enumerate(keys):
        b = pillars[k][1]
        notes = []
        if b in gm_year_set:
            notes.append("[年]공망")
        if b in gm_day_set:
            notes.append("[日]공망")
        if notes:
            lines.append(f"- **{PILLAR_NAMES[i]}지 {branch_hanja(b)}**: {', '.join(notes)}")

    lines.append("")

    # 신살
    shinsal = calc_shinsal_all(pillars)
    lines += [
        "### 신살",
    ]
    for pname in PILLAR_NAMES:
        ss = shinsal.get(pname, [])
        lines.append(f"- **{pname}주**: {', '.join(ss) if ss else '-'}")
    lines.append("")

    # 오행 결핍 특이사항
    missing = [oh for oh in oh_names if ohaeng[oh] == 0]
    if missing:
        lines.append("### 오행 결핍 특이사항")
        oh_meaning = {"목": "성장, 인성/겁재", "화": "표현력, 식상", "토": "안정, 재성/식상", "금": "결단, 관성/재성", "수": "지혜, 인성/식상"}
        for oh in missing:
            lines.append(f"- **{oh}({oh_hanja_map[oh]}) 완전 결핍**: {oh_meaning.get(oh, '')}")
        lines.append("")

    return "\n".join(lines)


# ─── 메인 ───

def main():
    parser = argparse.ArgumentParser(description="생년월일시로 만세력 데이터 자동 생성")
    parser.add_argument("--name", required=True, help="이름")
    parser.add_argument("--date", required=True, help="생년월일 (YYYY-MM-DD)")
    parser.add_argument("--time", required=True, help="태어난 시간 (HH:MM)")
    parser.add_argument("--gender", required=True, choices=["남", "여"], help="성별")

    args = parser.parse_args()

    try:
        birth = datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("오류: 날짜 형식은 YYYY-MM-DD입니다.")
        sys.exit(1)

    try:
        time_parts = args.time.split(":")
        hour, minute = int(time_parts[0]), int(time_parts[1])
    except (ValueError, IndexError):
        print("오류: 시간 형식은 HH:MM입니다.")
        sys.exit(1)

    y, m, d = birth.year, birth.month, birth.day

    pillars = get_four_pillars(y, m, d, hour, minute)
    daewoon = calc_daewoon(pillars, args.gender, y, m, d)

    md = generate_markdown(args.name, args.gender, y, m, d, hour, minute, pillars, daewoon)

    print(md)


if __name__ == "__main__":
    main()
