"""내 옷장 API.

등록 흐름(계획서 기능 1)
1. POST /clothes/analyze : 사진 업로드 → 배경 제거 → Vision AI 가 메타데이터 추출 (아직 저장 X)
2. 사용자가 화면에서 AI 결과를 확인·수정 (1차 검수)
3. POST /clothes          : 검수한 값 + analyze 가 돌려준 이미지 주소로 저장
"""

import asyncio
import logging
import time
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from PIL import UnidentifiedImageError
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import ClothingItem
from app.models.enums import Category, ClothingStatus
from pathlib import Path

from app.core.config import settings
from app.schemas.clothing import AnalyzeResponse, ClothingCreate, ClothingOut, ClothingUpdate, ReanalyzeRequest, ReanalyzeResponse
from app.services import images, storage
from app.services.vision import VisionError, analyze_clothing

router = APIRouter(prefix="/clothes", tags=["clothes"])
log = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024


def _get_owned(db: DbSession, user: CurrentUser, item_id: int) -> ClothingItem:
    item = db.get(ClothingItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "옷을 찾을 수 없습니다.")
    return item


@router.get("", response_model=list[ClothingOut])
def list_clothes(
    db: DbSession,
    user: CurrentUser,
    category: Category | None = None,
    status_: Annotated[ClothingStatus | None, Query(alias="status")] = None,
):
    q = select(ClothingItem).where(ClothingItem.user_id == user.id)
    if category:
        q = q.where(ClothingItem.category == category)
    if status_:
        q = q.where(ClothingItem.status == status_)
    return db.scalars(q.order_by(ClothingItem.created_at.desc())).all()


async def _run_analysis(jpeg: bytes):
    """(analysis, ai_raw, ai_error) — 실패해도 예외 대신 ai_error 로 돌려준다."""
    try:
        analysis, ai_raw = await run_in_threadpool(analyze_clothing, jpeg)
    except VisionError as e:
        return None, None, str(e)
    if not analysis.is_clothing:
        return analysis, ai_raw, "사진에서 옷을 찾지 못했어요. 옷이 잘 보이게 다시 찍어 주세요."
    return analysis, ai_raw, None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    user: CurrentUser,
    image: Annotated[UploadFile, File(description="옷 사진 (jpg/png/webp, 10MB 이하)")],
):
    """사진을 저장하고 배경 제거 + AI 분석 결과를 돌려준다. 옷장에는 아직 저장하지 않는다.

    AI 분석이 실패해도 이미지는 돌려주므로(ai_error 에 이유) 사용자가 직접 입력해 저장할 수 있다.
    """
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "jpg, png, webp 이미지만 올릴 수 있어요.")
    data = await image.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "10MB 이하 이미지만 올릴 수 있어요.")
    try:
        img = images.open_image(data)
    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "이미지를 열 수 없어요. 다른 사진으로 시도해 주세요.") from e

    original_jpeg = images.to_jpeg(img)
    original_url = storage.save_upload(user.id, original_jpeg, ".jpg")

    # 배경 제거(내 컴퓨터 CPU)와 AI 분석(Google 서버)을 동시에 돌려 기다리는 시간을 줄인다
    started = time.monotonic()

    async def timed_cutout():
        out = await run_in_threadpool(images.remove_background, img)
        log.info("배경 제거 %.1fs", time.monotonic() - started)
        return out

    async def timed_analysis():
        out = await _run_analysis(original_jpeg)
        log.info("AI 분석 %.1fs", time.monotonic() - started)
        return out

    cutout, (analysis, ai_raw, ai_error) = await asyncio.gather(timed_cutout(), timed_analysis())
    image_url = storage.save_upload(user.id, images.to_png(cutout), ".png") if cutout is not None else original_url

    return AnalyzeResponse(
        original_image_url=original_url,
        image_url=image_url,
        background_removed=cutout is not None,
        analysis=analysis,
        ai_raw=ai_raw,
        ai_error=ai_error,
    )


@router.post("/reanalyze", response_model=ReanalyzeResponse)
async def reanalyze(body: ReanalyzeRequest, user: CurrentUser):
    """이미 올린 사진으로 AI 분석만 다시 (서버 혼잡 등으로 실패했을 때)."""
    if not storage.is_owned_upload(user.id, body.image_url):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "이미지 주소가 올바르지 않아요. 사진을 다시 올려 주세요.")
    path = Path(settings.upload_dir) / body.image_url.removeprefix("/uploads/")
    jpeg = images.to_jpeg(images.open_image(path.read_bytes()))
    analysis, ai_raw, ai_error = await _run_analysis(jpeg)
    return ReanalyzeResponse(analysis=analysis, ai_raw=ai_raw, ai_error=ai_error)


@router.post("", response_model=ClothingOut, status_code=status.HTTP_201_CREATED)
def create_clothing(body: ClothingCreate, db: DbSession, user: CurrentUser):
    """analyze 결과를 사용자가 검수한 뒤 옷장에 저장."""
    for url in (body.image_url, body.original_image_url):
        if url is not None and not storage.is_owned_upload(user.id, url):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "이미지 주소가 올바르지 않아요. 사진을 다시 올려 주세요.")

    item = ClothingItem(user_id=user.id, **body.model_dump(mode="json"), is_verified=True)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=ClothingOut)
def get_clothing(item_id: int, db: DbSession, user: CurrentUser):
    return _get_owned(db, user, item_id)


@router.patch("/{item_id}", response_model=ClothingOut)
def update_clothing(item_id: int, body: ClothingUpdate, db: DbSession, user: CurrentUser):
    item = _get_owned(db, user, item_id)
    for key, value in body.model_dump(mode="json", exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clothing(item_id: int, db: DbSession, user: CurrentUser):
    item = _get_owned(db, user, item_id)
    db.delete(item)
    db.commit()
