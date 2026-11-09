"""오늘 날씨 가져오기 (Open-Meteo — 키 없이 무료, 한국은 기상청 모델 포함).

다른 날씨 API(예: 기상청 단기예보)로 바꾸려면 이 파일의 fetch_weather 만 같은 형식(WeatherOut)으로 돌려주게 바꾸면 된다.
"""

import logging
import time

import httpx

from app.core import clock
from app.schemas.weather import HourlyWeather, WeatherOut
from app.services.geocode import reverse_geocode

log = logging.getLogger(__name__)

API_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL_S = 20 * 60  # 같은 위치는 20분 동안 다시 묻지 않음
RAIN_POP = 50  # 강수확률이 이 이상이면 '비 예보'로 본다

# WMO 날씨 코드 → 한국어 (https://open-meteo.com/en/docs 의 Weather variable documentation)
WMO_KO = {
    0: "맑음",
    1: "대체로 맑음",
    2: "구름 조금",
    3: "흐림",
    45: "안개",
    48: "안개",
    51: "약한 이슬비",
    53: "이슬비",
    55: "강한 이슬비",
    56: "어는 이슬비",
    57: "어는 이슬비",
    61: "약한 비",
    63: "비",
    65: "강한 비",
    66: "어는 비",
    67: "어는 비",
    71: "약한 눈",
    73: "눈",
    75: "많은 눈",
    77: "싸락눈",
    80: "소나기",
    81: "소나기",
    82: "강한 소나기",
    85: "눈 소나기",
    86: "강한 눈 소나기",
    95: "뇌우",
    96: "우박 동반 뇌우",
    99: "우박 동반 뇌우",
}
WET_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99}


class WeatherError(Exception):
    """사용자에게 보여 줄 메시지를 담은 날씨 조회 실패."""


_cache: dict[tuple[float, float], tuple[float, WeatherOut]] = {}


def describe(code: int | None) -> str:
    return WMO_KO.get(code if code is not None else -1, "알 수 없음")


DEVICE_LOCATION = "현재 위치"  # 프런트가 위치 권한으로 얻은 좌표일 때 보내는 이름


async def fetch_weather(lat: float, lon: float, location_name: str | None = None) -> WeatherOut:
    if location_name in (None, DEVICE_LOCATION):  # 좌표만 있으면 동네 이름을 찾아 붙임
        location_name = await reverse_geocode(lat, lon) or location_name
    key = (round(lat, 2), round(lon, 2))  # 약 1km 단위로 묶어 캐시
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_TTL_S:
        return hit[1].model_copy(update={"location_name": location_name or hit[1].location_name})

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code",
        "hourly": "temperature_2m,apparent_temperature,precipitation_probability,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "Asia/Seoul",
        "forecast_days": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(API_URL, params=params)
            res.raise_for_status()
            data = res.json()
    except (httpx.HTTPError, ValueError) as e:
        log.warning("날씨 조회 실패: %s", e)
        raise WeatherError("날씨 정보를 가져오지 못했어요. 잠시 후 다시 시도해 주세요.") from e

    try:
        weather = _parse(data, lat, lon, location_name)
    except (KeyError, IndexError, TypeError) as e:
        log.warning("날씨 응답 형식 오류: %s", e)
        raise WeatherError("날씨 정보를 이해하지 못했어요.") from e

    _cache[key] = (time.monotonic(), weather)
    return weather


def _parse(data: dict, lat: float, lon: float, location_name: str | None) -> WeatherOut:
    cur, hourly, daily = data["current"], data["hourly"], data["daily"]
    now_hour = clock.now().hour

    hours: list[HourlyWeather] = []
    for i, t in enumerate(hourly["time"]):  # "2026-11-09T15:00"
        hours.append(
            HourlyWeather(
                hour=int(t[11:13]),
                temp=round(hourly["temperature_2m"][i]),
                feels_like=round(hourly["apparent_temperature"][i]),
                pop=hourly["precipitation_probability"][i] or 0,
                sky=describe(hourly["weather_code"][i]),
            )
        )

    # 지금 이후로 비(또는 눈)가 올 것 같은 시간대
    wet = [
        h.hour
        for h, code in zip(hours, hourly["weather_code"])
        if h.hour >= now_hour and (h.pop >= RAIN_POP or code in WET_CODES)
    ]
    rest = [h.pop for h in hours if h.hour >= now_hour]
    pop_rest = max(rest) if rest else 0
    rain_from = wet[0] if wet else None
    rain_until = wet[-1] if wet else None

    temp_max = round(daily["temperature_2m_max"][0])
    temp_min = round(daily["temperature_2m_min"][0])
    sky = describe(cur["weather_code"])
    if rain_from is not None and rain_from > now_hour:
        summary = f"{sky}, {rain_from}시부터 비 소식"
    elif rain_from is not None:
        summary = f"{sky}, {rain_until}시까지 비 소식" if rain_until != rain_from else sky
    else:
        summary = sky

    return WeatherOut(
        location_name=location_name,
        latitude=lat,
        longitude=lon,
        temp=round(cur["temperature_2m"]),
        feels_like=round(cur["apparent_temperature"]),
        sky=sky,
        summary=summary,
        temp_max=temp_max,
        temp_min=temp_min,
        temp_range=temp_max - temp_min,
        pop_max=daily["precipitation_probability_max"][0] or 0,
        pop_rest=pop_rest,
        rain_from=rain_from,
        rain_until=rain_until,
        hourly=[h for h in hours if 6 <= h.hour <= 23],
        fetched_at=clock.now(),
    )
