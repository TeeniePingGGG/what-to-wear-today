"""코디 추천 API (계획서 기능 2)."""

from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.core import clock
from app.models import Outfit, OutfitItem, Recommendation
from app.schemas.recommendation import RecommendationOut, RecommendRequest
from app.services.gemini import AIError
from app.services.recommender import RecommendError, recommend
from app.services.weather import WeatherError, fetch_weather

router = APIRouter(tags=["recommendations"])

_OUTFITS = selectinload(Recommendation.outfits)
_LOAD = [_OUTFITS.selectinload(Outfit.items).selectinload(OutfitItem.clothing_item), _OUTFITS.selectinload(Outfit.feedback)]


def load_recommendation(db: DbSession, rec_id: int) -> Recommendation:
    return db.scalars(select(Recommendation).options(*_LOAD).where(Recommendation.id == rec_id)).one()


@router.post("/recommendations", response_model=RecommendationOut, status_code=status.HTTP_201_CREATED)
async def create_recommendation(body: RecommendRequest, db: DbSession, user: CurrentUser):
    """오늘 날씨 + 일정 + 상황으로 내 옷장에서 코디 최대 3개를 추천받는다."""
    try:
        weather = await fetch_weather(body.latitude, body.longitude, body.location_name)
    except WeatherError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e)) from e
    try:
        rec = await run_in_threadpool(recommend, db, user, body, weather)
    except RecommendError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    except AIError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from e
    return load_recommendation(db, rec.id)


@router.get("/recommendations/today", response_model=RecommendationOut | None)
def today_recommendation(db: DbSession, user: CurrentUser):
    """오늘 받은 가장 최근 추천. 없으면 null."""
    q = (
        select(Recommendation)
        .options(*_LOAD)
        .where(Recommendation.user_id == user.id, Recommendation.target_date == clock.today())
        .order_by(Recommendation.id.desc())
        .limit(1)
    )
    return db.scalars(q).first()
