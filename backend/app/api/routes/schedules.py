"""오늘 일정 (계획서 기능 2의 입력). 지금은 직접 입력만, 캘린더 연동은 이후 단계."""

import datetime as dt

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core import clock
from app.models import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleOut

router = APIRouter(prefix="/schedules", tags=["schedules"])


def list_for_day(db: DbSession, user_id: int, day: dt.date) -> list[Schedule]:
    q = (
        select(Schedule)
        .where(Schedule.user_id == user_id, Schedule.date == day)
        .order_by(Schedule.start_time.is_(None), Schedule.start_time, Schedule.id)  # 시간 없는 일정은 뒤로
    )
    return list(db.scalars(q).all())


@router.get("", response_model=list[ScheduleOut])
def list_schedules(db: DbSession, user: CurrentUser, date: dt.date | None = None):
    """하루 일정 목록. date 를 비우면 오늘."""
    return list_for_day(db, user.id, date or clock.today())


@router.post("", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(body: ScheduleCreate, db: DbSession, user: CurrentUser):
    row = Schedule(user_id=user.id, **body.model_dump(exclude={"date"}), date=body.date or clock.today())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: DbSession, user: CurrentUser):
    row = db.get(Schedule, schedule_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "일정을 찾을 수 없어요.")
    db.delete(row)
    db.commit()
