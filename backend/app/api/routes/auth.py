from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: DbSession):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 가입된 이메일입니다.")
    user = User(email=body.email, password_hash=hash_password(body.password), nickname=body.nickname)
    db.add(user)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession):
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다.")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
