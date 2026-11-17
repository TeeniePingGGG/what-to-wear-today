from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _connect_args() -> dict:
    if not settings.db_ssl:
        return {}
    import certifi  # 공인 인증서 목록 (TiDB Cloud 같은 클라우드 DB 의 SSL 확인용)

    return {"ssl": {"ca": certifi.where()}}


engine = create_engine(
    settings.database_url,
    connect_args=_connect_args(),
    pool_pre_ping=True,
    pool_recycle=300,  # 클라우드 DB 는 쉬는 연결을 빨리 끊어서 짧게
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
