from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import Category, FeedbackRating, Mood, RecommendationStatus, str_enum


class Recommendation(Base):
    """코디 추천 요청 1회. 그 시점의 날씨·일정·상황을 스냅샷으로 남긴다."""

    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_recommendations_user_date", "user_id", "target_date"),
        {"comment": "코디 추천 요청"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)

    location_name: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))

    # {"temp":14,"feels_like":12,"min":9,"max":18,"pop":60,"sky":"맑음","rain_from":"15:00",...}
    weather: Mapped[dict] = mapped_column(JSON, nullable=False)
    # 추천 당시 일정 목록 복사본 (일정이 나중에 수정돼도 기록 유지)
    schedule_snapshot: Mapped[list | None] = mapped_column(JSON)
    situations: Mapped[list[str]] = mapped_column(JSON, nullable=False, comment='["발표","저녁 약속"]')
    mood: Mapped[Mood | None] = mapped_column(str_enum(Mood))
    user_note: Mapped[str | None] = mapped_column(String(500), comment="AI에게 더 알려줄 것")

    status: Mapped[RecommendationStatus] = mapped_column(
        str_enum(RecommendationStatus), nullable=False, server_default=RecommendationStatus.PENDING.value
    )
    llm_model: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    outfits = relationship(
        "Outfit", back_populates="recommendation", cascade="all, delete-orphan", order_by="Outfit.rank"
    )


class Outfit(Base):
    """추천 요청 1회에서 나온 코디 조합 (보통 3개) + AI 스타일리스트 가이드."""

    __tablename__ = "outfits"
    __table_args__ = (
        UniqueConstraint("recommendation_id", "rank", name="uq_outfits_rec_rank"),
        {"comment": "추천 코디 조합"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False
    )
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="1부터 시작하는 추천 순위")
    summary: Mapped[str | None] = mapped_column(String(300), comment="한 줄 추천 이유 (홈 카드)")
    intro: Mapped[str | None] = mapped_column(String(300), comment="스타일리스트 인사말 (가이드 화면)")
    # [{"tag":"기온","title":"일교차 9° — 레이어드","body":"..."}]
    reasons: Mapped[list | None] = mapped_column(JSON)
    tips: Mapped[list | None] = mapped_column(JSON, comment='["셔츠 소매를 한 번 접어...", ...]')

    is_selected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), comment="'이걸로 입을게요' 선택 여부"
    )
    selected_at: Mapped[datetime | None] = mapped_column(DateTime)

    recommendation = relationship("Recommendation", back_populates="outfits")
    items = relationship("OutfitItem", back_populates="outfit", cascade="all, delete-orphan")
    feedback = relationship("OutfitFeedback", back_populates="outfit", uselist=False, cascade="all, delete-orphan")


class OutfitItem(Base):
    """코디 조합 ↔ 옷 (N:M 연결 테이블)."""

    __tablename__ = "outfit_items"
    __table_args__ = {"comment": "코디 구성 아이템"}

    outfit_id: Mapped[int] = mapped_column(ForeignKey("outfits.id", ondelete="CASCADE"), primary_key=True)
    clothing_item_id: Mapped[int] = mapped_column(
        ForeignKey("clothing_items.id", ondelete="CASCADE"), primary_key=True
    )
    slot: Mapped[Category] = mapped_column(str_enum(Category), nullable=False, comment="코디 내 역할")

    outfit = relationship("Outfit", back_populates="items")
    clothing_item = relationship("ClothingItem")


class OutfitFeedback(TimestampMixin, Base):
    """코디에 대한 사용자 반응 — 다음 추천 프롬프트에 반영."""

    __tablename__ = "outfit_feedbacks"
    __table_args__ = {"comment": "코디 피드백"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    outfit_id: Mapped[int] = mapped_column(
        ForeignKey("outfits.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[FeedbackRating] = mapped_column(str_enum(FeedbackRating), nullable=False)
    reasons: Mapped[list | None] = mapped_column(JSON, comment='["TOO_COLD","TOO_FORMAL","IN_LAUNDRY"]')
    comment: Mapped[str | None] = mapped_column(String(500))

    outfit = relationship("Outfit", back_populates="feedback")
