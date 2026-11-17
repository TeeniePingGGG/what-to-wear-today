"""업로드한 옷 사진 저장소.

- STORAGE=local (기본, 내 컴퓨터): backend/uploads/{user_id}/파일 → URL '/uploads/{user_id}/파일'
- STORAGE=blob  (Vercel 배포): Vercel Blob 공개 저장소 → URL 'https://<store>.public.blob.vercel-storage.com/uploads/{user_id}/파일'
  Vercel 서버는 디스크에 파일을 남길 수 없어서 배포할 땐 blob 을 쓴다. (BLOB_READ_WRITE_TOKEN 필요)
"""

import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.core.config import settings

CONTENT_TYPES = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
BLOB_HOST_SUFFIX = ".public.blob.vercel-storage.com"


def _use_blob() -> bool:
    return settings.storage == "blob"


def save_upload(user_id: int, data: bytes, ext: str) -> str:
    filename = f"{uuid.uuid4().hex}{ext}"
    if _use_blob():
        from vercel.blob import sync as blob  # 배포 환경에서만 필요

        result = blob.put_blob(
            f"uploads/{user_id}/{filename}",
            data,
            access="public",
            content_type=CONTENT_TYPES.get(ext, "application/octet-stream"),
            cache_control_max_age=60 * 60 * 24 * 365,  # 파일 이름이 매번 달라서 오래 캐시해도 됨
        )
        return result.url

    folder = Path(settings.upload_dir) / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / filename).write_bytes(data)
    return f"/uploads/{user_id}/{filename}"


def _blob_name(user_id: int, url: str) -> str | None:
    """Blob URL 이 이 사용자 폴더의 파일이면 파일 이름, 아니면 None."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(BLOB_HOST_SUFFIX):
        return None
    path = unquote(parsed.path)
    prefix = f"/uploads/{user_id}/"
    if not path.startswith(prefix):
        return None
    name = path[len(prefix) :]
    if not name or "/" in name or "\\" in name or ".." in name:
        return None
    return name


def is_owned_upload(user_id: int, url: str) -> bool:
    """이 사용자가 올린 파일의 URL이 맞는지 (남의 파일·경로 조작 방지)."""
    if _use_blob():
        return _blob_name(user_id, url) is not None

    prefix = f"/uploads/{user_id}/"
    if not url.startswith(prefix):
        return False
    name = url[len(prefix) :]
    if not name or "/" in name or "\\" in name or ".." in name:
        return False
    return (Path(settings.upload_dir) / str(user_id) / name).is_file()


def read_upload(url: str) -> bytes:
    """저장해 둔 사진 내용 (is_owned_upload 로 검사한 URL 만 넘길 것)."""
    if _use_blob():
        from vercel.blob import sync as blob

        return blob.get_blob(url, access="public").body
    return (Path(settings.upload_dir) / url.removeprefix("/uploads/")).read_bytes()
