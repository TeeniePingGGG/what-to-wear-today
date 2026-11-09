from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Category, ClothingStatus, Season


class ClothingBase(BaseModel):
    name: str = Field(max_length=100)
    category: Category
    sub_category: str | None = Field(default=None, max_length=50)
    color_name: str | None = Field(default=None, max_length=30)
    color_hex: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    seasons: list[Season] = []
    styles: list[str] = []
    material: str | None = Field(default=None, max_length=50)
    warmth_level: int = Field(default=3, ge=1, le=5)
    is_waterproof: bool = False
    memo: str | None = Field(default=None, max_length=500)


class ClothingCreate(ClothingBase):
    """AI 분석(/clothes/analyze) 후 사용자가 검수한 값으로 저장."""

    image_url: str = Field(max_length=500, description="analyze 응답의 image_url")
    original_image_url: str | None = Field(default=None, max_length=500)
    ai_analysis: dict | None = Field(default=None, description="analyze 응답의 ai_raw (수정 전 AI 원본)")


class ClothingAnalysis(BaseModel):
    """Vision AI 가 돌려주는 형식 (Gemini response_schema 로도 사용)."""

    is_clothing: bool
    name: str
    category: Category
    sub_category: str | None = None
    color_name: str | None = None
    color_hex: str | None = None
    seasons: list[Season] = []
    styles: list[str] = []
    material: str | None = None
    warmth_level: int = 3
    is_waterproof: bool = False
    low_confidence_fields: list[str] = []

    @field_validator("warmth_level")
    @classmethod
    def _clamp_warmth(cls, v: int) -> int:
        return min(max(v, 1), 5)

    @field_validator("color_hex")
    @classmethod
    def _check_hex(cls, v: str | None) -> str | None:
        if v and len(v) == 7 and v.startswith("#"):
            try:
                int(v[1:], 16)
                return v.upper()
            except ValueError:
                pass
        return None

    @field_validator("name")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        return v.strip()[:100]


class AnalyzeResponse(BaseModel):
    original_image_url: str
    image_url: str = Field(description="배경 제거된 이미지 (실패 시 원본과 같음)")
    background_removed: bool
    analysis: ClothingAnalysis | None = Field(description="AI 분석 결과. 실패하면 null")
    ai_raw: dict | None = Field(description="저장할 때 ai_analysis 로 그대로 보내 주세요")
    ai_error: str | None = Field(description="AI 분석 실패 이유 (사용자 표시용)")


class ReanalyzeRequest(BaseModel):
    image_url: str = Field(max_length=500, description="analyze 응답의 image_url")


class ReanalyzeResponse(BaseModel):
    analysis: ClothingAnalysis | None
    ai_raw: dict | None
    ai_error: str | None


class ClothingUpdate(BaseModel):
    """사용자 검수/수정 — 보낸 필드만 바뀐다."""

    name: str | None = Field(default=None, max_length=100)
    category: Category | None = None
    sub_category: str | None = Field(default=None, max_length=50)
    color_name: str | None = Field(default=None, max_length=30)
    color_hex: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    seasons: list[Season] | None = None
    styles: list[str] | None = None
    material: str | None = Field(default=None, max_length=50)
    warmth_level: int | None = Field(default=None, ge=1, le=5)
    is_waterproof: bool | None = None
    status: ClothingStatus | None = None
    is_verified: bool | None = None
    memo: str | None = Field(default=None, max_length=500)


class ClothingOut(ClothingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    original_image_url: str | None
    ai_analysis: dict | None
    is_verified: bool
    status: ClothingStatus
    wear_count: int
    last_worn_at: date | None
    created_at: datetime
    updated_at: datetime
