import datetime as dt

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Index, String, Time, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import ScheduleSource, str_enum


class Schedule(TimestampMixin, Base):
    """사용자가 직접 입력했거나 캘린더에서 가져온 일정."""

    __tablename__ = "schedules"
    __table_args__ = (
        Index("ix_schedules_user_date", "user_id", "date"),
        UniqueConstraint("user_id", "source", "external_id", name="uq_schedules_external"),
        {"comment": "일정"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[dt.time | None] = mapped_column(Time)
    end_time: Mapped[dt.time | None] = mapped_column(Time)
    location: Mapped[str | None] = mapped_column(String(100))
    is_outdoor: Mapped[bool | None] = mapped_column(Boolean, comment="실외 일정 여부 (모르면 NULL)")
    is_important: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), comment="주요 일정 (코디 기준이 됨)"
    )
    source: Mapped[ScheduleSource] = mapped_column(
        str_enum(ScheduleSource), nullable=False, server_default=ScheduleSource.MANUAL.value
    )
    external_id: Mapped[str | None] = mapped_column(String(255), comment="외부 캘린더 이벤트 ID")
