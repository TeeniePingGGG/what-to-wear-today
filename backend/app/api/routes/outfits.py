"""추천된 코디 한 벌: 상세·가이드(기능 3)·입기 선택·피드백."""

from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.api.routes.recommendations import load_recommendation
from app.core import clock
from app.models import ClothingItem, Outfit, OutfitFeedback
from app.models.enums import ClothingStatus, FeedbackRating
from app.schemas.recommendation import FEEDBACK_REASONS, FeedbackIn, OutfitDetailOut, RecommendationOut
from app.services.gemini import AIError
from app.services.stylist import generate_guide

router = APIRouter(prefix="/outfits", tags=["outfits"])


def _get_owned(db: DbSession, user: CurrentUser, outfit_id: int) -> Outfit:
    outfit = db.get(Outfit, outfit_id)
    if outfit is None or outfit.recommendation.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "코디를 찾을 수 없어요.")
    return outfit


@router.get("/{outfit_id}", response_model=OutfitDetailOut)
def get_outfit(outfit_id: int, db: DbSession, user: CurrentUser):
    """코디 상세 (옷, 그날의 조건, 가이드, 피드백)."""
    return _get_owned(db, user, outfit_id)


@router.post("/{outfit_id}/guide", response_model=OutfitDetailOut)
async def create_guide(outfit_id: int, db: DbSession, user: CurrentUser, regenerate: bool = False):
    """AI 스타일리스트 가이드(추천 이유·연출 팁)를 만든다. 이미 있으면 그대로 돌려준다 (regenerate=true 면 새로)."""
    outfit = _get_owned(db, user, outfit_id)
    if outfit.reasons and not regenerate:
        return outfit
    try:
        return await run_in_threadpool(generate_guide, db, outfit)
    except AIError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from e


@router.post("/{outfit_id}/select", response_model=RecommendationOut)
def select_outfit(outfit_id: int, db: DbSession, user: CurrentUser):
    """'이걸로 입을게요' — 오늘 입을 코디로 정하고 옷마다 착용 기록을 남긴다. 같은 추천의 다른 코디는 선택 해제."""
    outfit = _get_owned(db, user, outfit_id)
    if outfit.is_selected:
        return load_recommendation(db, outfit.recommendation_id)

    today = clock.today()
    for other in outfit.recommendation.outfits:
        if other.is_selected:  # 마음을 바꾼 경우: 이전 선택의 착용 기록을 되돌림
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
    return load_recommendation(db, outfit.recommendation_id)


@router.put("/{outfit_id}/feedback", response_model=OutfitDetailOut)
def put_feedback(outfit_id: int, body: FeedbackIn, db: DbSession, user: CurrentUser):
    """좋아요/아쉬워요 피드백 저장 (다시 보내면 덮어씀). 다음 추천 때 AI에게 전달된다.

    '세탁 중' 이유와 함께 laundry_item_ids 를 보내면 그 옷들은 세탁 중으로 바뀌어 추천에서 빠진다.
    """
    outfit = _get_owned(db, user, outfit_id)
    unknown = [r for r in body.reasons if r not in FEEDBACK_REASONS]
    if unknown:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"알 수 없는 이유: {', '.join(unknown)}")
    reasons = body.reasons if body.rating == FeedbackRating.DISLIKE else []

    fb = outfit.feedback or OutfitFeedback(outfit=outfit, user_id=user.id)
    fb.rating = body.rating
    fb.reasons = reasons
    fb.comment = (body.comment or "").strip() or None
    db.add(fb)

    if "IN_LAUNDRY" in reasons and body.laundry_item_ids:
        in_outfit = {oi.clothing_item_id for oi in outfit.items}
        ids = [i for i in body.laundry_item_ids if i in in_outfit]  # 이 코디에 있는 내 옷만
        for item in db.scalars(select(ClothingItem).where(ClothingItem.id.in_(ids))).all():
            item.status = ClothingStatus.LAUNDRY
    db.commit()
    db.refresh(outfit)
    return outfit


@router.delete("/{outfit_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(outfit_id: int, db: DbSession, user: CurrentUser):
    """피드백 취소."""
    outfit = _get_owned(db, user, outfit_id)
    if outfit.feedback is not None:
        db.delete(outfit.feedback)
        db.commit()
