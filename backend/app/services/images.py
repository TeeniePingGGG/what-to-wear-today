"""이미지 전처리와 배경 제거.

배경 제거는 rembg(로컬 AI 모델)를 쓴다. requirements-bg.txt 를 설치하지 않았거나
실패하면 None 을 돌려주고, 등록은 원본 사진으로 계속 진행된다.
처음 실행할 때 모델 파일(약 170MB)을 내려받아서 첫 요청만 오래 걸린다.
"""

import io
import logging
import threading
import time

from PIL import Image, ImageOps

from app.core.config import settings

log = logging.getLogger(__name__)

MAX_SIDE = 1280  # 처리 속도와 용량을 위해 긴 변을 이 크기로 줄임

_session = None
_session_lock = threading.Lock()


def open_image(data: bytes) -> Image.Image:
    """사진을 열고 휴대폰 회전 정보(EXIF)를 반영해 바로 세운 뒤 크기를 줄인다."""
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    return img


def to_jpeg(img: Image.Image, quality: int = 88) -> bytes:
    """투명 배경은 흰색으로 채워 JPEG 로."""
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        img = bg
    else:
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def to_png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _get_session():
    global _session
    with _session_lock:
        if _session is None:
            from rembg import new_session  # 설치 안 됐으면 ImportError

            _session = new_session(settings.bg_model)
        return _session


def warm_up() -> None:
    """서버 시작 시 배경 제거 모델을 미리 불러 둔다 (첫 등록이 느리지 않도록). 백그라운드 스레드에서 호출."""
    if not settings.bg_removal:
        return
    try:
        started = time.monotonic()
        _get_session()
        log.info("배경 제거 모델 준비 완료 (%.1fs)", time.monotonic() - started)
    except ImportError:
        log.info("rembg 미설치 — 배경 제거 없이 동작 (pip install -r requirements-bg.txt)")
    except Exception:
        log.exception("배경 제거 모델 준비 실패")


def remove_background(img: Image.Image) -> Image.Image | None:
    """배경을 투명하게 지우고 옷 둘레만 남기도록 잘라낸 RGBA 이미지. 실패하면 None."""
    if not settings.bg_removal:
        return None
    try:
        from rembg import remove

        out = remove(img.convert("RGB"), session=_get_session())
    except ImportError:
        log.info("rembg 미설치 — 배경 제거 건너뜀 (pip install -r requirements-bg.txt)")
        return None
    except Exception:
        log.exception("배경 제거 실패")
        return None

    bbox = out.getchannel("A").point(lambda a: 255 if a > 10 else 0).getbbox()
    if bbox is None:  # 아무것도 못 찾음
        return None
    pad = round(max(out.size) * 0.04)
    left, top, right, bottom = bbox
    return out.crop((max(left - pad, 0), max(top - pad, 0), min(right + pad, out.width), min(bottom + pad, out.height)))
