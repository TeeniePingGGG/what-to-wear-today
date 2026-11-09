from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession, cred: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> User:
    user_id = decode_access_token(cred.credentials) if cred else None
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "로그인이 필요합니다.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
