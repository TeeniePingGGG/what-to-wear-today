"""DB에 문자열(VARCHAR + CHECK)로 저장되는 코드 값들.

프론트의 src/types/api.ts 에도 같은 값이 정의돼 있으니 바꿀 땐 함께 수정하세요.
"""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class Category(StrEnum):
    TOP = "TOP"  # 상의
    BOTTOM = "BOTTOM"  # 하의
    OUTER = "OUTER"  # 아우터
    DRESS = "DRESS"  # 원피스/셋업
    SHOES = "SHOES"  # 신발
    BAG = "BAG"  # 가방
    ACCESSORY = "ACCESSORY"  # 모자·머플러 등


class Season(StrEnum):
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    FALL = "FALL"
    WINTER = "WINTER"


class ClothingStatus(StrEnum):
    ACTIVE = "ACTIVE"  # 추천에 사용 가능
    LAUNDRY = "LAUNDRY"  # 세탁 중 — 추천에서 잠시 제외
    ARCHIVED = "ARCHIVED"  # 보관/처분 — 추천에서 제외, 기록은 유지


class ScheduleSource(StrEnum):
    MANUAL = "MANUAL"
    GOOGLE = "GOOGLE"


class Mood(StrEnum):
    COMFY = "COMFY"  # 편하게
    NEAT = "NEAT"  # 단정하게
    DRESSY = "DRESSY"  # 꾸민 듯


class RecommendationStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FeedbackRating(StrEnum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"


def str_enum(enum_cls: type[StrEnum], length: int = 20) -> SAEnum:
    """MySQL ENUM 대신 VARCHAR + CHECK 로 저장 (값 추가 시 마이그레이션이 단순함)."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
        name=enum_cls.__name__.lower(),
    )
