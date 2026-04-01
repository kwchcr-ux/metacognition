#!/usr/bin/env python3
"""
saju_calendar.py - 만세력 기반 간지 변환기
양력 날짜를 입력하면 세운(년운)/월운/일진을 간지로 변환한다.

사용법:
    python3 saju_calendar.py              # 오늘 날짜 기준
    python3 saju_calendar.py 2026-03-24   # 특정 날짜 지정
"""

import sys
from datetime import date, datetime

# ─── 기본 데이터 ───

CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

OHAENG = {
    "갑": "목", "을": "목", "병": "화", "정": "화", "무": "토",
    "기": "토", "경": "금", "신": "금", "임": "수", "계": "수",
}

JIJI_OHAENG = {
    "자": "수", "축": "토", "인": "목", "묘": "목", "진": "토", "사": "화",
    "오": "화", "미": "토", "신": "금", "유": "금", "술": "토", "해": "수",
}

TWELVE_ANIMALS = {
    "자": "쥐", "축": "소", "인": "호랑이", "묘": "토끼",
    "진": "용", "사": "뱀", "오": "말", "미": "양",
    "신": "원숭이", "유": "닭", "술": "개", "해": "돼지",
}

# 절기 월 이름
MONTH_NAMES = {
    1: "인월(寅月·입춘~경칩)",
    2: "묘월(卯月·경칩~청명)",
    3: "진월(辰月·청명~입하)",
    4: "사월(巳月·입하~망종)",
    5: "오월(午月·망종~소서)",
    6: "미월(未月·소서~입추)",
    7: "신월(申月·입추~백로)",
    8: "유월(酉月·백로~한로)",
    9: "술월(戌月·한로~입동)",
    10: "해월(亥月·입동~대설)",
    11: "자월(子月·대설~소한)",
    12: "축월(丑月·소한~입춘)",
}


# ─── 율리우스 적일 계산 ───

def julian_day_number(year: int, month: int, day: int) -> int:
    """그레고리력 날짜 → 율리우스 적일(JDN) 변환"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return (
        day
        + (153 * m + 2) // 5
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )


# ─── 절기 기반 월 판단 ───

def get_saju_month(month: int, day: int) -> int:
    """
    양력 월·일로 절기 기준 사주 월(1~12) 반환.
    1=인월, 2=묘월, ..., 12=축월

    ※ 절기 경계일은 연도마다 ±1일 차이가 있을 수 있음.
       정밀 분석 시 해당 연도의 정확한 절기 시각을 확인할 것.
    """
    boundaries = [
        # (시작월, 시작일, 사주월)
        (2, 4, 1),    # 입춘 → 인월
        (3, 6, 2),    # 경칩 → 묘월
        (4, 5, 3),    # 청명 → 진월
        (5, 6, 4),    # 입하 → 사월
        (6, 6, 5),    # 망종 → 오월
        (7, 7, 6),    # 소서 → 미월
        (8, 7, 7),    # 입추 → 신월
        (9, 8, 8),    # 백로 → 유월
        (10, 8, 9),   # 한로 → 술월
        (11, 7, 10),  # 입동 → 해월
        (12, 7, 11),  # 대설 → 자월
        (1, 6, 12),   # 소한 → 축월
    ]

    # 현재 날짜가 어떤 절기 구간에 속하는지 판단
    date_val = month * 100 + day

    if date_val >= 204 and date_val < 306:
        return 1
    elif date_val >= 306 and date_val < 405:
        return 2
    elif date_val >= 405 and date_val < 506:
        return 3
    elif date_val >= 506 and date_val < 606:
        return 4
    elif date_val >= 606 and date_val < 707:
        return 5
    elif date_val >= 707 and date_val < 807:
        return 6
    elif date_val >= 807 and date_val < 908:
        return 7
    elif date_val >= 908 and date_val < 1008:
        return 8
    elif date_val >= 1008 and date_val < 1107:
        return 9
    elif date_val >= 1107 and date_val < 1207:
        return 10
    elif date_val >= 1207:
        return 11
    elif date_val < 106:
        return 11  # 전년도 자월 계속
    else:
        return 12  # 1/6 ~ 2/3 → 축월


# ─── 년주 계산 ───

def get_year_ganji(year: int, month: int, day: int) -> tuple[str, str]:
    """
    년주 간지 계산 (입춘 기준).
    입춘(약 2/4) 이전이면 전년도 간지를 사용한다.
    """
    adj_year = year
    if month < 2 or (month == 2 and day < 4):
        adj_year -= 1

    stem_idx = (adj_year - 4) % 10
    branch_idx = (adj_year - 4) % 12
    return CHEONGAN[stem_idx], JIJI[branch_idx]


# ─── 월주 계산 ───

def get_month_ganji(year: int, month: int, day: int) -> tuple[str, str]:
    """
    월주 간지 계산 (절기 기준).
    년간에 따라 월간이 결정되고, 월지는 절기월에 고정된다.
    """
    # 입춘 기준 연도
    adj_year = year
    if month < 2 or (month == 2 and day < 4):
        adj_year -= 1

    saju_month = get_saju_month(month, day)

    # 월지: 인(2)부터 시작, saju_month=1 → 인(idx 2)
    branch_idx = (saju_month + 1) % 12

    # 월간: 년간에 따른 인월 시작 천간
    # 갑/기→병(2), 을/경→무(4), 병/신→경(6), 정/임→임(8), 무/계→갑(0)
    year_stem_idx = (adj_year - 4) % 10
    base_stem = ((year_stem_idx % 5) * 2 + 2) % 10
    stem_idx = (base_stem + saju_month - 1) % 10

    return CHEONGAN[stem_idx], JIJI[branch_idx]


# ─── 일주 계산 ───

def get_day_ganji(year: int, month: int, day: int) -> tuple[str, str]:
    """
    일주 간지 계산 (율리우스 적일 기반).
    검증: 2024-01-01 = 갑자일, 2000-01-01 = 무오일
    """
    jdn = julian_day_number(year, month, day)
    stem_idx = (jdn + 9) % 10
    branch_idx = (jdn + 1) % 12
    return CHEONGAN[stem_idx], JIJI[branch_idx]


# ─── 출력 포맷 ───

def _hanja(stem: str, branch: str) -> str:
    """한글 간지 → 한자 변환"""
    s_hanja = CHEONGAN_HANJA[CHEONGAN.index(stem)]
    b_hanja = JIJI_HANJA[JIJI.index(branch)]
    return f"{s_hanja}{b_hanja}"


def format_ganji(stem: str, branch: str) -> str:
    """간지 문자열 + 한자 + 오행 정보"""
    return f"{stem}{branch}({_hanja(stem, branch)}) [{OHAENG[stem]}{JIJI_OHAENG[branch]}]"


def format_ganji_detail(stem: str, branch: str) -> str:
    """간지 + 한자 + 오행 + 띠(지지용)"""
    animal = TWELVE_ANIMALS.get(branch, "")
    return f"{stem}{branch}({_hanja(stem, branch)}) [{OHAENG[stem]}{JIJI_OHAENG[branch]}] {animal}"


# ─── 메인 ───

def analyze(target_date: date) -> None:
    """주어진 날짜의 세운/월운/일진을 출력한다."""
    y, m, d = target_date.year, target_date.month, target_date.day

    year_stem, year_branch = get_year_ganji(y, m, d)
    month_stem, month_branch = get_month_ganji(y, m, d)
    day_stem, day_branch = get_day_ganji(y, m, d)
    saju_month = get_saju_month(m, d)

    print("=" * 50)
    print(f"  만세력 간지 변환 결과")
    print(f"  양력: {target_date.isoformat()} ({['월','화','수','목','금','토','일'][target_date.weekday()]}요일)")
    print("=" * 50)
    print()

    print(f"  ■ 세운(년운): {format_ganji_detail(year_stem, year_branch)}")
    print(f"    → {year_stem}{year_branch}({_hanja(year_stem, year_branch)})년 ({TWELVE_ANIMALS[year_branch]}띠 해)")
    print()

    print(f"  ■ 월운:       {format_ganji_detail(month_stem, month_branch)}")
    print(f"    → {MONTH_NAMES[saju_month]}")
    print()

    print(f"  ■ 일진:       {format_ganji_detail(day_stem, day_branch)}")
    print()

    print("-" * 50)
    print(f"  오행 요약:")
    all_chars = [year_stem, year_branch, month_stem, month_branch, day_stem, day_branch]
    ohaeng_count = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for ch in all_chars:
        oh = OHAENG.get(ch) or JIJI_OHAENG.get(ch, "")
        if oh:
            ohaeng_count[oh] += 1

    for oh, count in ohaeng_count.items():
        bar = "●" * count + "○" * (6 - count)
        print(f"    {oh}({oh[0]}): {bar} {count}")

    print("-" * 50)
    print()
    print("  ※ 절기 경계일(±1일)은 연도별 만세력으로 정확히 확인하세요.")
    print("  ※ 시주(時柱)는 출생 시간 기준이므로 여기서 계산하지 않습니다.")
    print()


def main():
    if len(sys.argv) > 1:
        try:
            target = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        except ValueError:
            print(f"오류: 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력하세요.")
            print(f"예시: python3 saju_calendar.py 2026-03-24")
            sys.exit(1)
    else:
        target = date.today()

    analyze(target)


if __name__ == "__main__":
    main()
