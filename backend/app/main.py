import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import auth, clothes, outfits, recommendations, schedules, weather
from app.core.config import settings
from app.db.session import engine
from app.services import images

# app.* 로거의 INFO 로그(처리 시간 등)를 터미널에 보이게
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     [%(name)s] %(message)s")
for _name in ("httpx", "httpx2"):  # 요청마다 찍히는 로그는 숨김
    logging.getLogger(_name).setLevel(logging.WARNING)



@asynccontextmanager
async def lifespan(_: FastAPI):
    # 배경 제거 모델(수십 MB)을 미리 메모리에 올려 둠 — 서버 시작은 막지 않도록 별도 스레드
    threading.Thread(target=images.warm_up, daemon=True).start()
    yield


app = FastAPI(title="오늘 뭐 입지? API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

api_prefix = "/api"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(clothes.router, prefix=api_prefix)
app.include_router(weather.router, prefix=api_prefix)
app.include_router(schedules.router, prefix=api_prefix)
app.include_router(recommendations.router, prefix=api_prefix)
app.include_router(outfits.router, prefix=api_prefix)


@app.get("/api/health", tags=["health"])
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}
