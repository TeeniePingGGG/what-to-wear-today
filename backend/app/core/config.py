from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "mysql+pymysql://wear:wear1234@localhost:3306/wear?charset=utf8mb4"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://localhost:5173"
    upload_dir: str = "uploads"

    # 기능1: Vision AI (Gemini) + 배경 제거
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"  # 주 모델이 붐비거나 한도 초과일 때
    gemini_thinking: str = "minimal"  # 모델의 생각 단계: minimal/low/medium/high, 비우면 모델 기본값
    bg_removal: bool = True
    bg_model: str = "u2net"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
