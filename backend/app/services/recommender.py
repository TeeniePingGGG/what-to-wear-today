"""AI 코디 추천 엔진 (계획서 기능 2).

내 옷장(보유 옷 목록) + 오늘 날씨 + 일정·상황을 LLM 에 주고, 옷 id 조합만 고르게 한다.
LLM 이 돌려준 id 는 반드시 서버에서 다시 검증한다 → '내가 가진 옷으로만' 추천을 보장.
"""

import json
import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.models import ClothingItem, Outfit, OutfitFeedback, OutfitItem, Recommendation, Schedule, User
from app.models.enums import Category, ClothingStatus, FeedbackRating, Mood, RecommendationStatus
from app.schemas.recommendation import FEEDBACK_REASONS, OutfitPick, OutfitPicks, RecommendRequest
from app.schemas.weather import WeatherOut
from app.services.gemini import AIError, generate

log = logging.getLogger(__name__)

MAX_OUTFITS = 3
RECENT_DAYS = 2  # 최근 이틀 안에 입은 옷은 되도록 피함

MOOD_KO = {Mood.COMFY: "편하게", Mood.NEAT: "단정하게", Mood.DRESSY: "꾸민 듯"}
SEASON_KO = {"SPRING": "봄", "SUMMER": "여름", "FALL": "가을", "WINTER": "겨울"}
# 한 코디에 한 개만 들어갈 수 있는 종류
SINGLE_SLOTS = {Category.TOP, Category.BOTTOM, Category.DRESS, Category.OUTER, Category.SHOES, Category.BAG}

PROMPT = """너는 친절한 패션 스타일리스트야. 사용자가 **이미 가진 옷** 중에서만 오늘 입을 코디를 골라 줘.

## 오늘 날씨 ({location})
{weather}

## 오늘 일정
{schedules}

## 오늘의 상황·원하는 분위기
- 상황: {situations}
- 분위기: {mood}
- 사용자 메모: {note}

## 사용자가 최근 남긴 코디 피드백 (참고해서 취향과 체감에 맞춰)
{feedback}

## 사용자의 옷장 (JSON, id 로 고르기)
{closet}

## 규칙
1. item_ids 에는 위 옷장 목록에 있는 id 만 써. 목록에 없는 옷은 절대 만들지 마.
2. 코디마다 [상의(TOP) 1개 + 하의(BOTTOM) 1개] 또는 [원피스·셋업(DRESS) 1개]가 꼭 있어야 해.
3. 아우터(OUTER)·신발(SHOES)·가방(BAG)은 각각 최대 1개, 액세서리(ACCESSORY)는 최대 2개.
   - 체감 온도가 낮거나(대략 17°C 이하) 일교차가 크거나 비 소식이 있으면 아우터를 넣어.
   - 신발이 옷장에 있으면 넣어. 비 소식이 있으면 방수(is_waterproof) 옷·신발을 우선해.
4. 보온성(warmth_level 1~5)과 계절(seasons)이 오늘 기온에 맞아야 해.
5. 일정·상황·분위기에 어울려야 해 (예: 발표·면접은 단정하게, 운동·많이 걷기는 편하게).
6. worn_recently 가 true 인 옷은 다른 선택지가 없을 때만 써.
   피드백에서 '추울 것 같아요'가 있었으면 비슷한 기온에서 더 따뜻하게, '더울 것 같아요'면 더 가볍게 골라.
   '아쉬워요'를 받은 조합은 그대로 반복하지 말고, '좋아요'를 받은 옷·조합 스타일은 참고해.
7. 서로 다른 코디를 최대 {max_outfits}개, 가장 좋은 것부터 순서대로. 코디끼리 옷이 2개 이상은 달라야 해.
8. summary: 왜 이 조합인지 날씨·일정을 근거로 한국어 1~2문장, 80자 이내. 옷 이름을 자연스럽게 넣어.
"""


def feedback_text(db: Session, user_id: int, days: int = 30, limit: int = 8) -> str:
    """최근 피드백 요약 (추천 프롬프트용). 없으면 '없음'."""
    since = clock.today() - timedelta(days=days)
    q = (
        select(OutfitFeedback)
        .join(Outfit, Outfit.id == OutfitFeedback.outfit_id)
        .join(Recommendation, Recommendation.id == Outfit.recommendation_id)
        .where(OutfitFeedback.user_id == user_id, Recommendation.target_date >= since)
        .order_by(OutfitFeedback.updated_at.desc())
        .limit(limit)
    )
    lines = []
    for fb in db.scalars(q).all():
        outfit = fb.outfit
        rec = outfit.recommendation
        names = " + ".join(oi.clothing_item.name for oi in outfit.items)
        w = rec.weather or {}
        cond = f"{rec.target_date.month}/{rec.target_date.day}, 체감 {w.get('feels_like', '?')}°C"
        if fb.rating == FeedbackRating.LIKE:
            verdict = "좋아요"
        else:
            reasons = [FEEDBACK_REASONS.get(r, r) for r in (fb.reasons or [])]
            verdict = "아쉬워요" + (f" ({', '.join(reasons)})" if reasons else "")
        comment = f' — "{fb.comment}"' if fb.comment else ""
        lines.append(f"- {cond}: {names} → {verdict}{comment}")
    return "\n".join(lines) if lines else "- 아직 없음"


class RecommendError(Exception):
    """사용자에게 보여 줄 메시지 (옷장이 부족한 경우 등)."""


def _closet(db: Session, user_id: int) -> list[ClothingItem]:
    q = select(ClothingItem).where(
        ClothingItem.user_id == user_id,
        ClothingItem.status == ClothingStatus.ACTIVE,
        ClothingItem.is_verified.is_(True),
    )
    return list(db.scalars(q).all())


def _check_enough(items: list[ClothingItem]) -> None:
    cats = {i.category for i in items}
    if Category.DRESS in cats or {Category.TOP, Category.BOTTOM} <= cats:
        return
    missing = [name for cat, name in ((Category.TOP, "상의"), (Category.BOTTOM, "하의")) if cat not in cats]
    raise RecommendError(f"코디를 만들려면 {'와 '.join(missing)}를 1벌 이상 등록해 주세요.")


def weather_text(w: WeatherOut) -> str:
    def part(hours: range) -> str:
        hs = [h for h in w.hourly if h.hour in hours]
        if not hs:
            return "-"
        return f"{min(h.temp for h in hs)}~{max(h.temp for h in hs)}°C, 강수확률 최대 {max(h.pop for h in hs)}%"

    rain = "없음"
    if w.rain_from is not None:
        rain = f"{w.rain_from}시부터" + (f" {w.rain_until}시까지" if w.rain_until and w.rain_until != w.rain_from else "")
    return "\n".join(
        [
            f"- 지금: {w.temp}°C (체감 {w.feels_like}°C), {w.sky}",
            f"- 최저 {w.temp_min}°C / 최고 {w.temp_max}°C (일교차 {w.temp_range}°C)",
            f"- 남은 시간 최고 강수확률 {w.pop_rest}%, 비 소식: {rain}",
            f"- 아침(6~11시) {part(range(6, 12))}",
            f"- 오후(12~17시) {part(range(12, 18))}",
            f"- 저녁(18~23시) {part(range(18, 24))}",
        ]
    )


def _schedule_snapshot(rows: list[Schedule]) -> list[dict]:
    return [
        {
            "title": s.title,
            "start_time": s.start_time.strftime("%H:%M") if s.start_time else None,
            "end_time": s.end_time.strftime("%H:%M") if s.end_time else None,
            "location": s.location,
            "is_outdoor": s.is_outdoor,
            "is_important": s.is_important,
        }
        for s in rows
    ]


def schedule_text(snapshot: list[dict]) -> str:
    if not snapshot:
        return "- 등록된 일정 없음"
    lines = []
    for s in snapshot:
        when = s["start_time"] or "시간 미정"
        if s["end_time"]:
            when += f"~{s['end_time']}"
        extra = [x for x in (s["location"], "실외" if s["is_outdoor"] else None, "★주요 일정" if s["is_important"] else None) if x]
        lines.append(f"- {when} {s['title']}" + (f" ({', '.join(extra)})" if extra else ""))
    return "\n".join(lines)


def _closet_json(items: list[ClothingItem]) -> str:
    recent = clock.today() - timedelta(days=RECENT_DAYS)
    rows = [
        {
            "id": i.id,
            "name": i.name,
            "category": i.category.value,
            "sub_category": i.sub_category,
            "color": i.color_name,
            "seasons": [SEASON_KO.get(s, s) for s in i.seasons],
            "styles": i.styles,
            "material": i.material,
            "warmth_level": i.warmth_level,
            "is_waterproof": i.is_waterproof,
            "worn_recently": bool(i.last_worn_at and i.last_worn_at >= recent),
        }
        for i in items
    ]
    return json.dumps(rows, ensure_ascii=False)


def _validate(pick: OutfitPick, by_id: dict[int, ClothingItem]) -> list[ClothingItem] | None:
    """보유 옷 id 인지, 종류 조합이 말이 되는지 검사. 고칠 수 있으면 고치고, 안 되면 None."""
    chosen: list[ClothingItem] = []
    used_slots: dict[Category, int] = {}
    for item_id in dict.fromkeys(pick.item_ids):  # 중복 제거, 순서 유지
        item = by_id.get(item_id)
        if item is None:
            log.warning("AI가 옷장에 없는 id %s 를 골라서 뺌", item_id)
            continue
        limit = 1 if item.category in SINGLE_SLOTS else 2
        if used_slots.get(item.category, 0) >= limit:
            continue
        used_slots[item.category] = used_slots.get(item.category, 0) + 1
        chosen.append(item)

    has_dress = Category.DRESS in used_slots
    has_set = Category.TOP in used_slots and Category.BOTTOM in used_slots
    if not (has_dress or has_set):
        return None
    if has_dress and has_set:  # 원피스 + 상하의가 섞이면 원피스를 뺌
        chosen = [i for i in chosen if i.category != Category.DRESS]
    return chosen


def recommend(db: Session, user: User, req: RecommendRequest, weather: WeatherOut) -> Recommendation:
    closet = _closet(db, user.id)
    _check_enough(closet)
    today = clock.today()
    schedules = list(
        db.scalars(
            select(Schedule)
            .where(Schedule.user_id == user.id, Schedule.date == today)
            .order_by(Schedule.start_time.is_(None), Schedule.start_time)
        ).all()
    )
    snapshot = _schedule_snapshot(schedules)

    prompt = PROMPT.format(
        location=weather.location_name or req.location_name or "현재 위치",
        weather=weather_text(weather),
        schedules=schedule_text(snapshot),
        situations=", ".join(req.situations) or "특별한 상황 없음",
        mood=MOOD_KO.get(req.mood, "상관없음") if req.mood else "상관없음",
        note=req.user_note or "없음",
        feedback=feedback_text(db, user.id),
        closet=_closet_json(closet),
        max_outfits=MAX_OUTFITS,
    )
    picks, model = generate([prompt], OutfitPicks, temperature=0.6)

    by_id = {i.id: i for i in closet}
    outfits: list[tuple[list[ClothingItem], str]] = []
    seen: set[frozenset[int]] = set()
    for pick in picks.outfits:
        chosen = _validate(pick, by_id)
        if not chosen:
            continue
        key = frozenset(i.id for i in chosen)
        if key in seen:
            continue
        seen.add(key)
        outfits.append((chosen, pick.summary.strip()[:300]))
        if len(outfits) == MAX_OUTFITS:
            break
    if not outfits:
        raise AIError("AI가 알맞은 코디를 고르지 못했어요. 다시 시도해 주세요.")

    rec = Recommendation(
        user_id=user.id,
        target_date=today,
        location_name=weather.location_name or req.location_name,
        latitude=req.latitude,
        longitude=req.longitude,
        weather=weather.model_dump(mode="json"),
        schedule_snapshot=snapshot,
        situations=req.situations,
        mood=req.mood,
        user_note=req.user_note,
        status=RecommendationStatus.COMPLETED,
        llm_model=model,
    )
    for rank, (chosen, summary) in enumerate(outfits, start=1):
        outfit = Outfit(rank=rank, summary=summary)
        outfit.items = [OutfitItem(clothing_item=i, slot=i.category) for i in chosen]
        rec.outfits.append(outfit)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
