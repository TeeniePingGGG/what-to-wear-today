import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Category, FeedbackRating, Mood, RecommendationStatus


class RecommendRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: str | None = Field(default=None, max_length=100)
    situations: list[str] = Field(default=[], max_length=10, description='오늘의 상황 (예: ["발표", "저녁 약속"])')
    mood: Mood | None = None
    user_note: str | None = Field(default=None, max_length=500, description="AI에게 더 알려줄 것")


# --- LLM 이 돌려주는 형식 (Gemini response_schema) ---
class OutfitPick(BaseModel):
    item_ids: list[int] = Field(description="이 코디에 쓰는 옷 id 목록 (옷장 목록에 있는 id 만)")
    summary: str = Field(description="이 코디를 고른 이유 한두 문장")


class OutfitPicks(BaseModel):
    outfits: list[OutfitPick]


# 피드백 이유 코드 → 한국어 (프런트 src/types/api.ts 와 같게)
FEEDBACK_REASONS = {
    "TOO_COLD": "추울 것 같아요",
    "TOO_HOT": "더울 것 같아요",
    "TOO_FORMAL": "너무 격식 있어요",
    "TOO_CASUAL": "너무 편해 보여요",
    "DONT_LIKE_COMBO": "색·조합이 별로예요",
    "IN_LAUNDRY": "세탁 중인 옷이 있어요",
}


class GuideReason(BaseModel):
    tag: str = Field(description="짧은 분류: 기온 / 비 / 일정 / 분위기 / 색 조합 / 소재 중 하나")
    title: str = Field(description="20자 이내 소제목")
    body: str = Field(description="70자 이내 설명")


class Guide(BaseModel):
    """AI 스타일리스트 가이드 (Gemini response_schema, 계획서 기능 3)."""

    intro: str = Field(description="친근한 인사와 오늘 코디 한 줄 소개, 80자 이내")
    reasons: list[GuideReason] = Field(description="이 코디를 고른 이유 2~4개")
    tips: list[str] = Field(description="이 옷들로 할 수 있는 구체적인 연출 팁 2~3개, 각 60자 이내")


class FeedbackIn(BaseModel):
    rating: FeedbackRating
    reasons: list[str] = Field(default=[], max_length=10, description=f"이유 코드: {', '.join(FEEDBACK_REASONS)}")
    comment: str | None = Field(default=None, max_length=500)
    laundry_item_ids: list[int] = Field(default=[], max_length=10, description="세탁 중으로 바꿀 옷 id (IN_LAUNDRY 일 때)")


# --- API 응답 ---
class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rating: FeedbackRating
    reasons: list[str] | None
    comment: str | None
    updated_at: dt.datetime


class OutfitClothingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: Category
    sub_category: str | None
    color_name: str | None
    color_hex: str | None
    image_url: str


class OutfitItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slot: Category
    clothing_item: OutfitClothingOut


class OutfitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rank: int
    summary: str | None
    intro: str | None = Field(description="스타일리스트 인사말 (가이드를 만들기 전엔 null)")
    reasons: list[GuideReason] | None = Field(description="상세 추천 이유 (가이드를 만들기 전엔 null)")
    tips: list[str] | None = Field(description="스타일링 팁 (가이드를 만들기 전엔 null)")
    is_selected: bool
    items: list[OutfitItemOut]
    feedback: FeedbackOut | None


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_date: dt.date
    location_name: str | None
    weather: dict
    schedule_snapshot: list | None
    situations: list[str]
    mood: Mood | None
    user_note: str | None
    status: RecommendationStatus
    created_at: dt.datetime
    outfits: list[OutfitOut]


class RecommendationContextOut(BaseModel):
    """코디 상세 화면에서 보여 줄 '그날의 조건'."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    target_date: dt.date
    location_name: str | None
    weather: dict
    schedule_snapshot: list | None
    situations: list[str]
    mood: Mood | None


class OutfitDetailOut(OutfitOut):
    recommendation: RecommendationContextOut
