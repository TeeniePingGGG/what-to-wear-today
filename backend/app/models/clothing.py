from datetime import date

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import Category, ClothingStatus, str_enum


class ClothingItem(TimestampMixin, Base):
    """내 옷장의 옷 한 벌. Vision AI 분석 결과 + 사용자 검수 결과가 저장된다."""

    __tablename__ = "clothing_items"
    __table_args__ = (
        CheckConstraint("warmth_level BETWEEN 1 AND 5", name="warmth_level_range"),
        Index("ix_clothing_items_user_category", "user_id", "category"),
        Index("ix_clothing_items_user_status", "user_id", "status"),
        {"comment": "옷장 아이템"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="예: 옥스퍼드 셔츠")
    category: Mapped[Category] = mapped_column(str_enum(Category), nullable=False)
    sub_category: Mapped[str | None] = mapped_column(String(50), comment="예: 라운드넥 니트")
    color_name: Mapped[str | None] = mapped_column(String(30), comment="예: 네이비")
    color_hex: Mapped[str | None] = mapped_column(String(7), comment="#2C3A57")
    seasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, comment='["FALL","WINTER"]')
    styles: Mapped[list[str]] = mapped_column(JSON, nullable=False, comment='["미니멀","캐주얼"]')
    material: Mapped[str | None] = mapped_column(String(50), comment="예: 울 혼방")
    warmth_level: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("3"), comment="보온성 1(얇음)~5(매우 두꺼움)"
    )
    is_waterproof: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))

    image_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="배경 제거된 이미지")
    original_image_url: Mapped[str | None] = mapped_column(String(500), comment="원본 업로드 이미지")

    # Vision AI 원본 응답(JSON) — 필드별 신뢰도 포함. 사용자가 고친 값과 비교·재학습용
    ai_analysis: Mapped[dict | None] = mapped_column(JSON)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), comment="사용자 검수 완료 여부"
    )

    status: Mapped[ClothingStatus] = mapped_column(
        str_enum(ClothingStatus), nullable=False, server_default=ClothingStatus.ACTIVE.value
    )
    wear_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    last_worn_at: Mapped[date | None] = mapped_column(Date)
    memo: Mapped[str | None] = mapped_column(String(500))

    user = relationship("User", back_populates="clothing_items")
