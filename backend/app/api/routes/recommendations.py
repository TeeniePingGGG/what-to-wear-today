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

_LOAD = selectinload(Recommendation.outfits).selectinload(Outfit.items).selectinload(OutfitItem.clothing_item)


def _load(db: DbSession, rec_id: int) -> Recommendation:
    return db.scalars(select(Recommendation).options(_LOAD).where(Recommendation.id == rec_id)).one()


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
    return _load(db, rec.id)


@router.get("/recommendations/today", response_model=RecommendationOut | None)
def today_recommendation(db: DbSession, user: CurrentUser):
    """오늘 받은 가장 최근 추천. 없으면 null."""
    q = (
        select(Recommendation)
        .options(_LOAD)
        .where(Recommendation.user_id == user.id, Recommendation.target_date == clock.today())
        .order_by(Recommendation.id.desc())
        .limit(1)
    )
    return db.scalars(q).first()


@router.post("/outfits/{outfit_id}/select", response_model=RecommendationOut)
def select_outfit(outfit_id: int, db: DbSession, user: CurrentUser):
    """'이걸로 입을게요' — 오늘 입을 코디로 정하고 옷마다 착용 기록을 남긴다. 같은 추천의 다른 코디는 선택 해제."""
    outfit = db.get(Outfit, outfit_id)
    if outfit is None or outfit.recommendation.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "코디를 찾을 수 없어요.")
    if outfit.is_selected:
        return _load(db, outfit.recommendation_id)

    today = clock.today()
    for other in outfit.recommendation.outfits:
        if other.is_selected:  # 마음을 바꾼 경우: 이전 선택의 착용 횟수를 되돌림
            other.is_selected = False
            other.selected_at = None
            for oi in other.items:
                oi.clothing_item.wear_count = max(oi.clothing_item.wear_count - 1, 0)
                if oi.clothing_item.last_worn_at == today:
                    oi.clothing_item.last_worn_at = None

    outfit.is_selected = True
    outfit.selected_at = clock.now().replace(tzinfo=None)
    for oi in outfit.items:
        oi.clothing_item.wear_count += 1
        oi.clothing_item.last_worn_at = today
    db.commit()
    return _load(db, outfit.recommendation_id)
