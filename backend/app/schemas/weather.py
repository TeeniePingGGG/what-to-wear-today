from datetime import date, datetime

from pydantic import BaseModel, Field


class HourlyWeather(BaseModel):
    hour: int = Field(description="0~23시")
    temp: int
    feels_like: int
    pop: int = Field(description="강수확률 %")
    sky: str


class WeatherOut(BaseModel):
    location_name: str | None
    latitude: float
    longitude: float
    forecast_date: date | None = Field(default=None, description="예보 날짜 (오늘 또는 내일)")
    temp: int = Field(description="현재 기온 °C (내일이면 아침 8시 예보)")
    feels_like: int = Field(description="현재 체감 온도 °C (내일이면 아침 8시 예보)")
    sky: str = Field(description="현재 하늘 상태 (예: 맑음, 내일이면 아침 8시)")
    summary: str = Field(description="한 줄 요약 (예: 맑음, 15시부터 비 소식)")
    temp_max: int
    temp_min: int
    temp_range: int = Field(description="일교차")
    pop_max: int = Field(description="오늘 하루 최고 강수확률 % (이미 지난 시간 포함)")
    pop_rest: int = Field(description="지금부터 남은 시간의 최고 강수확률 % (내일이면 하루 전체)")
    rain_from: int | None = Field(description="지금 이후 비가 시작될 시각(시). 없으면 null")
    rain_until: int | None
    hourly: list[HourlyWeather] = Field(description="6~23시 시간별 예보")
    fetched_at: datetime
