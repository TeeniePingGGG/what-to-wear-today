import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ScheduleSource


class ScheduleCreate(BaseModel):
    date: dt.date | None = Field(default=None, description="비우면 오늘(한국 시간)")
    title: str = Field(min_length=1, max_length=100)
    start_time: dt.time | None = None
    end_time: dt.time | None = None
    location: str | None = Field(default=None, max_length=100)
    is_outdoor: bool | None = Field(default=None, description="실외 일정이면 true, 모르면 null")
    is_important: bool = Field(default=False, description="코디 기준이 되는 주요 일정")


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: dt.date
    title: str
    start_time: dt.time | None
    end_time: dt.time | None
    location: str | None
    is_outdoor: bool | None
    is_important: bool
    source: ScheduleSource
