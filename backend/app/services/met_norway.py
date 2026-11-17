"""예비 날씨: 노르웨이 기상청(MET Norway) Locationforecast — 키 없이 무료.

Open-Meteo 에 접속이 안 될 때만 쓴다. 응답을 Open-Meteo 와 같은 모양으로 바꿔서
weather._parse 를 그대로 쓸 수 있게 한다.
문서: https://api.met.no/weatherapi/locationforecast/2.0/documentation
(User-Agent 헤더가 없으면 막히므로 꼭 넣는다)
"""

from datetime import datetime

import httpx

from app.core import clock
from app.services.geocode import USER_AGENT

API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"

# MET 날씨 기호(symbol_code) → Open-Meteo 와 같은 WMO 코드
SYMBOL_TO_WMO = {
    "clearsky": 0,
    "fair": 1,
    "partlycloudy": 2,
    "cloudy": 3,
    "fog": 45,
    "lightrain": 61,
    "rain": 63,
    "heavyrain": 65,
    "lightrainshowers": 80,
    "rainshowers": 81,
    "heavyrainshowers": 82,
    "lightsleet": 71,
    "sleet": 73,
    "heavysleet": 75,
    "lightsleetshowers": 85,
    "sleetshowers": 85,
    "heavysleetshowers": 86,
    "lightsnow": 71,
    "snow": 73,
    "heavysnow": 75,
    "lightsnowshowers": 85,
    "snowshowers": 85,
    "heavysnowshowers": 86,
}


def _wmo(symbol: str | None) -> int | None:
    if not symbol:
        return None
    base = symbol.split("_")[0]  # "rain_day" → "rain"
    if "thunder" in base:
        return 95
    return SYMBOL_TO_WMO.get(base)


def _feels_like(temp: float, wind_ms: float | None) -> float:
    """체감 온도 (기상청과 같은 겨울철 풍속 냉각 공식). 조건이 안 맞으면 기온 그대로."""
    if wind_ms is None:
        return temp
    v = wind_ms * 3.6  # km/h
    if temp > 10 or v <= 4.8:
        return temp
    return 13.12 + 0.6215 * temp - 11.37 * v**0.16 + 0.3965 * temp * v**0.16


def _pop(data: dict) -> int:
    for period in ("next_1_hours", "next_6_hours", "next_12_hours"):
        details = data.get(period, {}).get("details", {})
        if details.get("probability_of_precipitation") is not None:
            return round(details["probability_of_precipitation"])
    amount = data.get("next_1_hours", {}).get("details", {}).get("precipitation_amount")
    return 70 if amount and amount >= 0.1 else 0


async def fetch_met(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    """MET 예보를 받아 Open-Meteo 응답 모양(current/hourly/daily)으로 돌려준다."""
    res = await client.get(
        API_URL,
        params={"lat": round(lat, 4), "lon": round(lon, 4)},  # 소수점 4자리까지만 허용
        headers={"User-Agent": USER_AGENT},
    )
    res.raise_for_status()
    series = res.json()["properties"]["timeseries"]

    days = (clock.today(), clock.tomorrow())  # 오늘 + 내일 (Open-Meteo forecast_days=2 와 같게)
    times, temps, feels, pops, codes = [], [], [], [], []
    for entry in series:
        t = datetime.fromisoformat(entry["time"].replace("Z", "+00:00")).astimezone(clock.KST)
        if t.date() not in days:
            continue
        d = entry["data"]
        inst = d["instant"]["details"]
        temp = inst["air_temperature"]
        symbol = (d.get("next_1_hours") or d.get("next_6_hours") or {}).get("summary", {}).get("symbol_code")
        times.append(t.strftime("%Y-%m-%dT%H:00"))
        temps.append(temp)
        feels.append(_feels_like(temp, inst.get("wind_speed")))
        pops.append(_pop(d))
        codes.append(_wmo(symbol))

    if not times:
        raise ValueError("오늘·내일 MET 예보가 없음")

    # 날짜별 최고·최저 기온과 최고 강수확률 (오늘은 지난 시간 예보가 없어 남은 시간 기준)
    daily_days = sorted({x[:10] for x in times})
    by_day = {k: [i for i, x in enumerate(times) if x.startswith(k)] for k in daily_days}
    return {
        "current": {"temperature_2m": temps[0], "apparent_temperature": feels[0], "weather_code": codes[0]},
        "hourly": {
            "time": times,
            "temperature_2m": temps,
            "apparent_temperature": feels,
            "precipitation_probability": pops,
            "weather_code": codes,
        },
        "daily": {
            "time": daily_days,
            "temperature_2m_max": [max(temps[i] for i in by_day[k]) for k in daily_days],
            "temperature_2m_min": [min(temps[i] for i in by_day[k]) for k in daily_days],
            "precipitation_probability_max": [max(pops[i] for i in by_day[k]) for k in daily_days],
        },
    }
