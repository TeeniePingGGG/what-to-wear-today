import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Category, Mood, RecommendationStatus


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


# --- API 응답 ---
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
    reasons: list | None = Field(description="상세 추천 이유 (기능 3에서 채움)")
    tips: list | None = Field(description="스타일링 팁 (기능 3에서 채움)")
    is_selected: bool
    items: list[OutfitItemOut]


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
