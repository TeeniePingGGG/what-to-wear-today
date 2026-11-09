from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

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
