from decimal import Decimal

from sqlalchemy import BigInteger, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "회원"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(30), nullable=False)

    # 날씨 조회용 기본 위치 (브라우저 위치 권한이 없을 때 사용)
    default_location_name: Mapped[str | None] = mapped_column(String(100), comment="예: 서울 마포구")
    default_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    default_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))

    preferred_styles: Mapped[list[str] | None] = mapped_column(JSON, comment='선호 스타일 ["미니멀", ...]')

    clothing_items = relationship("ClothingItem", back_populates="user", cascade="all, delete-orphan")
