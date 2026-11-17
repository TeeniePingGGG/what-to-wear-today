"""한국 시간 기준 '오늘'과 '지금'. (서버가 어느 나라에 있든 사용자 기준은 한국)"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")  # Windows 는 tzdata 패키지가 있어야 동작


def now() -> datetime:
    return datetime.now(KST)


def today() -> date:
    return now().date()


def tomorrow() -> date:
    return today() + timedelta(days=1)


def plan_day(day: date | None) -> date:
    """코디를 볼 날짜: 비우면 오늘. 날씨 예보가 있는 오늘·내일만 허용."""
    if day is None:
        return today()
    if day not in (today(), tomorrow()):
        raise ValueError("오늘이나 내일만 고를 수 있어요.")
    return day


def day_label(day: date) -> str:
    """AI 프롬프트·화면용 이름: 오늘 / 내일 / 날짜."""
    if day == today():
        return "오늘"
    if day == tomorrow():
        return "내일"
    return f"{day.month}월 {day.day}일"
