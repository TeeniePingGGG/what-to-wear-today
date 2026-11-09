"""AI 스타일리스트 가이드와 피드백 (계획서 기능 3).

- generate_guide : 고른 코디가 왜 오늘 날씨·일정에 맞는지 설명하고, 연출 팁을 만든다.
(피드백을 다음 추천에 반영하는 부분은 recommender.feedback_text)
"""

import logging
from sqlalchemy.orm import Session

from app.models import Outfit, Recommendation
from app.schemas.recommendation import Guide
from app.schemas.weather import WeatherOut
from app.services.gemini import generate
from app.services.recommender import MOOD_KO, schedule_text, weather_text

log = logging.getLogger(__name__)

GUIDE_PROMPT = """너는 '오늘 뭐 입지?' 앱의 친절한 패션 스타일리스트야. 해요체로 다정하게 말해.
사용자가 오늘 입을 코디를 이미 골랐어. 이 코디가 왜 오늘에 어울리는지 설명하고, 연출 팁을 알려 줘.

## 오늘 날씨 ({location})
{weather}

## 오늘 일정
{schedules}

## 상황·분위기
- 상황: {situations}
- 분위기: {mood}
- 사용자 메모: {note}

## 고른 코디
{items}

## 작성 규칙
- intro: 인사 + 오늘 코디 한 줄 소개, 80자 이내.
- reasons: 2~4개. tag 는 "기온", "비", "일정", "분위기", "색 조합", "소재" 중 하나.
  날씨 숫자(기온, 체감, 일교차, 강수 시각)와 일정을 구체적으로 근거로 들어. 비 소식이 없으면 "비" 태그는 쓰지 마.
- tips: 2~3개. 위 옷들로 바로 할 수 있는 구체적인 연출법 (소매 걷기, 넣어 입기, 레이어링, 색 맞추기 등).
  코디에 없는 옷이나 새 아이템을 사라는 말은 하지 마.
- 과장하거나 확실하지 않은 정보(브랜드, 가격 등)는 쓰지 마.
"""


def _weather_of(rec: Recommendation) -> WeatherOut:
    data = dict(rec.weather)
    data.setdefault("pop_rest", data.get("pop_max", 0))  # 예전 기록 호환
    return WeatherOut.model_validate(data)


def _items_text(outfit: Outfit) -> str:
    lines = []
    for oi in outfit.items:
        c = oi.clothing_item
        extra = [x for x in (c.color_name, c.material, f"보온성 {c.warmth_level}/5", "생활방수" if c.is_waterproof else None) if x]
        lines.append(f"- [{oi.slot.value}] {c.name} ({', '.join(extra)})")
    return "\n".join(lines)


def generate_guide(db: Session, outfit: Outfit) -> Outfit:
    rec = outfit.recommendation
    prompt = GUIDE_PROMPT.format(
        location=rec.location_name or "현재 위치",
        weather=weather_text(_weather_of(rec)),
        schedules=schedule_text(rec.schedule_snapshot or []),
        situations=", ".join(rec.situations) or "특별한 상황 없음",
        mood=MOOD_KO.get(rec.mood, "상관없음") if rec.mood else "상관없음",
        note=rec.user_note or "없음",
        items=_items_text(outfit),
    )
    guide, model = generate([prompt], Guide, temperature=0.7)
    outfit.intro = guide.intro.strip()[:300]
    outfit.reasons = [r.model_dump() for r in guide.reasons[:4]]
    outfit.tips = [t.strip() for t in guide.tips[:3] if t.strip()]
    db.commit()
    log.info("가이드 생성 (outfit %s, %s)", outfit.id, model)
    return outfit
