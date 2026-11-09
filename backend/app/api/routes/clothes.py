"""내 옷장 API.

등록 흐름(계획서 기능 1)
1. POST /clothes/analyze : 사진 업로드 → Vision AI 가 옷을 전부 찾아 정보 추출 → 한 벌씩 잘라 배경 제거 (아직 저장 X)
2. 사용자가 화면에서 옷마다 AI 결과를 확인·수정 (1차 검수)
3. POST /clothes/bulk     : 고른 옷들을 한 번에 저장 (한 벌만이면 POST /clothes 도 가능)
"""

import logging
import time
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import ClothingItem
from app.models.enums import Category, ClothingStatus
from app.core.config import settings
from app.schemas.clothing import (
    AnalyzedItem,
    ClothingAnalysis,
    ClothingBulkCreate,
    ClothingCreate,
    ClothingOut,
    ClothingUpdate,
    MultiAnalyzeResponse,
    ReanalyzeRequest,
    ReanalyzeResponse,
    RedetectRequest,
)
from app.services import images, storage
from app.services.vision import VisionError, analyze_clothing, detect_clothes

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


CATEGORY_ORDER = {c: i for i, c in enumerate(["OUTER", "TOP", "DRESS", "BOTTOM", "SHOES", "BAG", "ACCESSORY"])}


async def _cutout_item(user_id: int, img: Image.Image) -> tuple[str, bool]:
    """배경을 지워 저장. (이미지 주소, 배경 제거 성공 여부)"""
    cutout = await run_in_threadpool(images.remove_background, img)
    if cutout is not None:
        return storage.save_upload(user_id, images.to_png(cutout), ".png"), True
    return storage.save_upload(user_id, images.to_jpeg(img), ".jpg"), False


async def _detect_and_cut(user_id: int, img: Image.Image, original_url: str) -> MultiAnalyzeResponse:
    """사진 속 옷을 전부 찾아 한 벌씩 잘라내고 배경을 지운다 (계획서 기능 1, 여러 벌 한 번에).

    AI 가 실패하거나 옷을 못 찾으면 사진 전체를 한 벌로 돌려줘서 사용자가 직접 입력할 수 있게 한다.
    """
    started = time.monotonic()
    ai_error = None
    detected = []
    model = None
    try:
        result, model = await run_in_threadpool(detect_clothes, images.to_jpeg(img))
        detected = sorted(result.items, key=lambda d: CATEGORY_ORDER.get(d.category, 99))
        log.info("AI 감지 %.1fs — %d벌", time.monotonic() - started, len(detected))
    except VisionError as e:
        ai_error = str(e)

    items: list[AnalyzedItem] = []
    for d in detected:
        crop = images.crop_box(img, d.box_2d)
        if crop is None:
            continue
        image_url, removed = await _cutout_item(user_id, crop)
        analysis = ClothingAnalysis.model_validate(d.model_dump(exclude={"box_2d"}))
        ai_raw = {"model": model, "result": analysis.model_dump(mode="json"), "box_2d": d.box_2d}
        items.append(AnalyzedItem(image_url=image_url, background_removed=removed, analysis=analysis, ai_raw=ai_raw))

    if not items:  # AI 실패 또는 옷을 못 찾음 → 사진 전체를 한 벌로
        if ai_error is None:
            ai_error = "사진에서 옷을 찾지 못했어요. 옷이 잘 보이게 다시 찍거나 직접 입력해 주세요."
        image_url, removed = await _cutout_item(user_id, img)
        items.append(AnalyzedItem(image_url=image_url, background_removed=removed, analysis=None, ai_raw=None))

    log.info("등록 분석 완료 %.1fs", time.monotonic() - started)
    return MultiAnalyzeResponse(original_image_url=original_url, items=items, ai_error=ai_error)


def _check_owned(user_id: int, url: str | None) -> None:
    if url is not None and not storage.is_owned_upload(user_id, url):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "이미지 주소가 올바르지 않아요. 사진을 다시 올려 주세요.")


def _load_upload(url: str) -> Image.Image:
    return images.open_image((Path(settings.upload_dir) / url.removeprefix("/uploads/")).read_bytes())


@router.post("/analyze", response_model=MultiAnalyzeResponse)
async def analyze(
    user: CurrentUser,
    image: Annotated[UploadFile, File(description="옷 사진 (jpg/png/webp, 10MB 이하). 여러 벌을 같이 찍어도 됨")],
):
    """사진 속 옷을 전부 찾아 한 벌씩 잘라 배경을 지우고 AI 분석 결과를 돌려준다. 옷장에는 아직 저장하지 않는다."""
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "jpg, png, webp 이미지만 올릴 수 있어요.")
    data = await image.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "10MB 이하 이미지만 올릴 수 있어요.")
    try:
        img = images.open_image(data)
    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "이미지를 열 수 없어요. 다른 사진으로 시도해 주세요.") from e

    original_url = storage.save_upload(user.id, images.to_jpeg(img), ".jpg")
    return await _detect_and_cut(user.id, img, original_url)


@router.post("/redetect", response_model=MultiAnalyzeResponse)
async def redetect(body: RedetectRequest, user: CurrentUser):
    """이미 올린 원본 사진으로 옷 찾기를 다시 (AI 서버 혼잡 등으로 실패했을 때)."""
    _check_owned(user.id, body.original_image_url)
    return await _detect_and_cut(user.id, _load_upload(body.original_image_url), body.original_image_url)


@router.post("/reanalyze", response_model=ReanalyzeResponse)
async def reanalyze(body: ReanalyzeRequest, user: CurrentUser):
    """잘라낸 옷 한 벌만 AI 분석을 다시."""
    _check_owned(user.id, body.image_url)
    analysis, ai_raw, ai_error = await _run_analysis(images.to_jpeg(_load_upload(body.image_url)))
    return ReanalyzeResponse(analysis=analysis, ai_raw=ai_raw, ai_error=ai_error)


@router.post("/bulk", response_model=list[ClothingOut], status_code=status.HTTP_201_CREATED)
def create_clothes_bulk(body: ClothingBulkCreate, db: DbSession, user: CurrentUser):
    """여러 벌을 한 번에 저장 (하나라도 문제가 있으면 아무것도 저장하지 않음)."""
    for it in body.items:
        _check_owned(user.id, it.image_url)
        _check_owned(user.id, it.original_image_url)
    rows = [ClothingItem(user_id=user.id, **it.model_dump(mode="json"), is_verified=True) for it in body.items]
    db.add_all(rows)
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows


@router.post("", response_model=ClothingOut, status_code=status.HTTP_201_CREATED)
def create_clothing(body: ClothingCreate, db: DbSession, user: CurrentUser):
    """analyze 결과를 사용자가 검수한 뒤 옷장에 저장."""
    _check_owned(user.id, body.image_url)
    _check_owned(user.id, body.original_image_url)

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
