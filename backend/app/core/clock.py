"""한국 시간 기준 '오늘'과 '지금'. (서버가 어느 나라에 있든 사용자 기준은 한국)"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")  # Windows 는 tzdata 패키지가 있어야 동작


def now() -> datetime:
    return datetime.now(KST)


def today() -> date:
    return now().date()
