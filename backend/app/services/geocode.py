"""위도·경도 → '서울 마포구' 같은 동네 이름 (역지오코딩).

OpenStreetMap 의 Nominatim 을 쓴다 (무료, 키 없음).
사용 규칙: 초당 1회 이하, 앱을 알아볼 수 있는 User-Agent 필수 → 결과를 캐시해서 같은 동네는 다시 묻지 않는다.
https://operations.osmfoundation.org/policies/nominatim/
실패하면 None 을 돌려주고, 화면에는 '현재 위치'가 그대로 보인다.
"""

import logging

import httpx

log = logging.getLogger(__name__)

API_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "what-to-wear-today/0.1 (student project)"

# 시·도 이름 줄이기: 서울특별시 → 서울, 경기도 → 경기
_SUFFIXES = ("특별자치시", "특별자치도", "특별시", "광역시", "도")
_cache: dict[tuple[float, float], str | None] = {}


def _short_city(name: str) -> str:
    for suffix in _SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix) + 1:
            return name[: -len(suffix)]
    return name


def format_address(addr: dict) -> str | None:
    """Nominatim address → '서울 마포구', '수원시 영통구', '경기 가평군' 등."""
    city = addr.get("city") or addr.get("town")
    district = addr.get("borough") or addr.get("city_district") or addr.get("county") or addr.get("district")
    province = addr.get("province") or addr.get("state")

    if city and district:
        parts = [_short_city(city), district]
    elif city:
        parts = [_short_city(province), city] if province and not city.startswith(_short_city(province)) else [_short_city(city)]
    elif district:
        parts = [_short_city(province), district] if province else [district]
    elif province:
        parts = [_short_city(province)]
    else:
        return None
    # '서울 서울' 같은 중복 제거
    out: list[str] = []
    for p in parts:
        if p and p not in out:
            out.append(p)
    return " ".join(out) or None


async def reverse_geocode(lat: float, lon: float) -> str | None:
    key = (round(lat, 2), round(lon, 2))  # 약 1km 단위로 묶어 캐시
    if key in _cache:
        return _cache[key]
    params = {"format": "jsonv2", "lat": lat, "lon": lon, "zoom": 14, "accept-language": "ko"}
    try:
        async with httpx.AsyncClient(timeout=5, headers={"User-Agent": USER_AGENT}) as client:
            res = await client.get(API_URL, params=params)
            res.raise_for_status()
            name = format_address(res.json().get("address") or {})
    except (httpx.HTTPError, ValueError) as e:
        log.warning("위치 이름 조회 실패: %s", e)
        return None  # 실패는 캐시하지 않음 (다음에 다시 시도)
    _cache[key] = name
    return name
