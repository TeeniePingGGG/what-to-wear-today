"""Vercel 배포용 진입점 — Vercel 은 이 파일의 `app` 을 찾아 실행한다.

내 컴퓨터에서는 지금처럼 `uvicorn app.main:app --reload --port 8000` 으로 실행하면 된다.
"""

from app.main import app

__all__ = ["app"]
