"""내 옷장 API.

등록 흐름(계획서 기능 1)
1. POST /clothes/analyze : 사진 업로드 → Vision AI 가 옷을 전부 찾아 정보 추출 → 한 벌씩 잘라 배경 제거 (아직 저장 X)
2. 사용자가 화면에서 옷마다 AI 결과를 확인·수정 (1차 검수)
3. POST /clothes/bulk     : 고른 옷들을 한 번에 저장 (한 벌만이면 POST /clothes 도 가능)

배포 서버처럼 서버에서 배경을 못 지울 때(background_removed=false)는
브라우저가 GET /clothes/image 로 잘린 사진을 받아 직접 배경을 지운 뒤
POST /clothes/cutout 으로 올려 새 주소를 받는다.
"""

import asyncio
import io
import logging
import time
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import ClothingItem
from app.models.enums import Category, ClothingStatus
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


def _cutout_item_sync(user_id: int, img: Image.Image) -> tuple[str, bool]:
    cutout = images.remove_background(img)
    if cutout is not None:
        return storage.save_upload(user_id, images.to_png(cutout), ".png"), True
    return storage.save_upload(user_id, images.to_jpeg(img), ".jpg"), False


async def _cutout_item(user_id: int, img: Image.Image) -> tuple[str, bool]:
    """배경을 지워 저장. (이미지 주소, 배경 제거 성공 여부) — 저장(Blob 업로드)까지 스레드에서"""
    return await run_in_threadpool(_cutout_item_sync, user_id, img)


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

    crops = [(d, images.crop_box(img, d.box_2d)) for d in detected]
    crops = [(d, c) for d, c in crops if c is not None]
    # 여러 벌을 동시에 자르고 저장 (한 벌씩 차례로 하면 벌 수만큼 느려짐)
    saved = await asyncio.gather(*(_cutout_item(user_id, c) for _, c in crops))
    items: list[AnalyzedItem] = []
    for (d, _), (image_url, removed) in zip(crops, saved):
        analysis = ClothingAnalysis.model_validate(d.model_dump(exclude={"box_2d"}))
        ai_raw = {"model": model, "result": analysis.model_dump(mode="json"), "box_2d": d.box_2d}
        items.append(AnalyzedItem(image_url=image_url, background_removed=removed, analysis=analysis, ai_raw=ai_raw))
    log.info("자르기·저장 완료 %.1fs — %d벌", time.monotonic() - started, len(items))

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
    return images.open_image(storage.read_upload(url))


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


CUTOUT_MAX_BYTES = 4 * 1024 * 1024  # Vercel 요청 크기 제한(4.5MB) 안쪽


@router.get("/image", response_class=Response)
def get_upload_image(user: CurrentUser, url: Annotated[str, Query(max_length=500)]):
    """내가 올린 사진 내용을 그대로 돌려준다 (브라우저 배경 제거용, 같은 주소라 CORS 걱정 없음)."""
    _check_owned(user.id, url)
    media_type = "image/png" if url.lower().endswith(".png") else "image/jpeg"
    return Response(storage.read_upload(url), media_type=media_type, headers={"Cache-Control": "private, max-age=600"})


@router.post("/cutout")
async def upload_cutout(
    user: CurrentUser,
    image: Annotated[UploadFile, File(description="브라우저에서 배경을 지운 PNG (4MB 이하)")],
) -> dict[str, str]:
    """브라우저가 배경을 지운 옷 사진을 저장하고 새 주소를 돌려준다."""
    data = await image.read()
    if len(data) > CUTOUT_MAX_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "배경을 지운 사진이 너무 커요.")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "이미지를 열 수 없어요.") from e
    if img.format != "PNG" or "A" not in img.getbands():
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "투명 배경 PNG 만 올릴 수 있어요.")
    img.thumbnail((images.MAX_SIDE, images.MAX_SIDE))
    return {"image_url": storage.save_upload(user.id, images.to_png(img), ".png")}


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
