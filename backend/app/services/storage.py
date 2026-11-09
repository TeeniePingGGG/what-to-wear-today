"""업로드 파일 저장 위치 관리. URL 형식: /uploads/{user_id}/{파일명}"""

import uuid
from pathlib import Path

from app.core.config import settings


def save_upload(user_id: int, data: bytes, ext: str) -> str:
    folder = Path(settings.upload_dir) / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (folder / filename).write_bytes(data)
    return f"/uploads/{user_id}/{filename}"


def is_owned_upload(user_id: int, url: str) -> bool:
    """이 사용자가 올린 파일의 URL이 맞는지 (남의 파일·경로 조작 방지)."""
    prefix = f"/uploads/{user_id}/"
    if not url.startswith(prefix):
        return False
    name = url[len(prefix) :]
    if not name or "/" in name or "\\" in name or ".." in name:
        return False
    return (Path(settings.upload_dir) / str(user_id) / name).is_file()
