"""오늘·내일 날씨 가져오기 (Open-Meteo — 키 없이 무료, 한국은 기상청 모델 포함).

다른 날씨 API(예: 기상청 단기예보)로 바꾸려면 이 파일의 fetch_weather 만 같은 형식(WeatherOut)으로 돌려주게 바꾸면 된다.
"""

import asyncio
import logging
import time
from datetime import date

import httpx

from app.core import clock
from app.schemas.weather import HourlyWeather, WeatherOut
from app.services.geocode import reverse_geocode
from app.services.met_norway import fetch_met

log = logging.getLogger(__name__)

API_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL_S = 20 * 60  # 같은 위치는 20분 동안 다시 묻지 않음
RETRIES = 2  # Open-Meteo 재시도 횟수 (그래도 안 되면 MET Norway)
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


# 위치별 원본 응답(오늘·내일 2일치) 캐시 — 날짜별로 그때그때 정리
_cache: dict[tuple[float, float], tuple[float, dict]] = {}
COMMUTE_HOUR = 8  # 내일 날씨는 '지금' 대신 출근·등교 시간 기준으로 보여 줌


def describe(code: int | None) -> str:
    return WMO_KO.get(code if code is not None else -1, "알 수 없음")


DEVICE_LOCATION = "현재 위치"  # 프런트가 위치 권한으로 얻은 좌표일 때 보내는 이름


async def fetch_weather(
    lat: float,
    lon: float,
    location_name: str | None = None,
    raw: dict | None = None,
    day: date | None = None,
) -> WeatherOut:
    """day(오늘·내일)의 날씨. 비우면 오늘.

    raw: 브라우저가 Open-Meteo 에서 직접 받아 온 응답 (오늘·내일 2일치).
    배포 서버(Vercel)에서는 Open-Meteo 접속이 자주 막혀서(ConnectTimeout),
    브라우저가 받아 온 값이 있으면 그걸 쓰고 없을 때만 서버가 직접 가져온다.
    """
    day = day or clock.today()
    if location_name in (None, DEVICE_LOCATION):  # 좌표만 있으면 동네 이름을 찾아 붙임
        location_name = await reverse_geocode(lat, lon) or location_name
    key = (round(lat, 2), round(lon, 2))  # 약 1km 단위로 묶어 캐시
    if raw is not None:
        try:
            weather = _parse(raw, lat, lon, location_name, day)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            log.warning("브라우저가 보낸 날씨 형식 오류, 서버에서 다시 조회: %r", e)
        else:
            _cache[key] = (time.monotonic(), raw)
            return weather
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_TTL_S:
        try:
            return _parse(hit[1], lat, lon, location_name, day)
        except (KeyError, IndexError, TypeError, ValueError):
            pass  # 캐시에 그 날짜가 없으면 새로 조회

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code",
        "hourly": "temperature_2m,apparent_temperature,precipitation_probability,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "Asia/Seoul",
        "forecast_days": 2,  # 오늘 + 내일 (프런트 src/api/openMeteo.ts 와 같게)
    }
    data = None
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=httpx.Timeout(8, connect=4)) as client:
        for attempt in range(1, RETRIES + 1):
            try:
                res = await client.get(API_URL, params=params)
                res.raise_for_status()
                data = res.json()
                break
            except (httpx.HTTPError, ValueError) as e:
                last_error = e
                # 타임아웃 오류는 메시지가 비어 있어서 종류(repr)까지 남김
                log.warning("날씨 조회 실패 (%d/%d번째): %r", attempt, RETRIES, e)
                if attempt < RETRIES:
                    await asyncio.sleep(0.5)
        if data is None:  # Open-Meteo 가 안 되면 노르웨이 기상청으로
            try:
                data = await fetch_met(client, lat, lon)
                log.info("Open-Meteo 대신 MET Norway 날씨 사용")
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as e:
                last_error = e
                log.warning("예비 날씨(MET Norway) 조회도 실패: %r", e)
    if data is None and hit:  # 오래된 캐시라도 있으면 그걸 보여 줌
        log.warning("날씨 API 응답 없음 - 이전에 받아 둔 날씨로 대신 표시")
        data = hit[1]
    if data is None:
        raise WeatherError("날씨 정보를 가져오지 못했어요. 잠시 후 다시 시도해 주세요.") from last_error

    try:
        weather = _parse(data, lat, lon, location_name, day)
    except (KeyError, IndexError, TypeError, ValueError) as e:
        log.warning("날씨 응답 형식 오류: %r", e)
        raise WeatherError("날씨 정보를 이해하지 못했어요.") from e

    _cache[key] = (time.monotonic(), data)
    return weather


def _parse(data: dict, lat: float, lon: float, location_name: str | None, day: date) -> WeatherOut:
    """Open-Meteo 형식 응답에서 day 하루치만 정리한다 (응답에 그 날이 없으면 ValueError)."""
    cur, hourly, daily = data["current"], data["hourly"], data["daily"]
    is_today = day == clock.today()
    now_hour = clock.now().hour if is_today else 0  # 내일은 하루 전체가 '남은 시간'
    prefix = day.isoformat()  # "2026-11-18"

    idx = [i for i, t in enumerate(hourly["time"]) if t.startswith(prefix)]
    if not idx:
        raise ValueError(f"{prefix} 예보가 응답에 없음")
    codes = [hourly["weather_code"][i] for i in idx]
    hours = [
        HourlyWeather(
            hour=int(hourly["time"][i][11:13]),  # "2026-11-09T15:00"
            temp=round(hourly["temperature_2m"][i]),
            feels_like=round(hourly["apparent_temperature"][i]),
            pop=hourly["precipitation_probability"][i] or 0,
            sky=describe(hourly["weather_code"][i]),
        )
        for i in idx
    ]

    # 지금(내일이면 0시) 이후로 비(또는 눈)가 올 것 같은 시간대
    wet = [h.hour for h, code in zip(hours, codes) if h.hour >= now_hour and (h.pop >= RAIN_POP or code in WET_CODES)]
    rest = [h.pop for h in hours if h.hour >= now_hour]
    pop_rest = max(rest) if rest else 0
    rain_from = wet[0] if wet else None
    rain_until = wet[-1] if wet else None

    d = daily["time"].index(prefix) if "time" in daily else (0 if is_today else 1)
    temp_max = round(daily["temperature_2m_max"][d])
    temp_min = round(daily["temperature_2m_min"][d])
    if is_today:
        now_temp, now_feels, now_code = cur["temperature_2m"], cur["apparent_temperature"], cur["weather_code"]
    else:  # 내일은 출근·등교 시간(없으면 가장 가까운 시간) 기준
        h = min(hours, key=lambda x: abs(x.hour - COMMUTE_HOUR))
        k = idx[hours.index(h)]
        now_temp, now_feels, now_code = h.temp, h.feels_like, hourly["weather_code"][k]
    sky = describe(now_code)
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
        forecast_date=day,
        temp=round(now_temp),
        feels_like=round(now_feels),
        sky=sky,
        summary=summary,
        temp_max=temp_max,
        temp_min=temp_min,
        temp_range=temp_max - temp_min,
        pop_max=daily["precipitation_probability_max"][d] or 0,
        pop_rest=pop_rest,
        rain_from=rain_from,
        rain_until=rain_until,
        hourly=[h for h in hours if 6 <= h.hour <= 23],
        fetched_at=clock.now(),
    )
