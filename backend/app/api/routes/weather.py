from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.schemas.weather import WeatherOut
from app.services.weather import WeatherError, fetch_weather

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("", response_model=WeatherOut)
async def get_weather(
    _: CurrentUser,
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    location_name: Annotated[str | None, Query(max_length=100)] = None,
):
    """위치의 오늘 날씨 (한국 시간 기준)."""
    try:
        return await fetch_weather(lat, lon, location_name)
    except WeatherError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e)) from e


class WeatherRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: str | None = Field(default=None, max_length=100)
    raw: dict | None = Field(default=None, description="브라우저가 Open-Meteo 에서 받아 온 원본 응답")


@router.post("", response_model=WeatherOut)
async def post_weather(_: CurrentUser, body: WeatherRequest):
    """브라우저가 받아 온 Open-Meteo 응답을 정리해 돌려준다. raw 가 없으면 서버가 직접 조회."""
    try:
        return await fetch_weather(body.latitude, body.longitude, body.location_name, body.raw)
    except WeatherError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e)) from e
