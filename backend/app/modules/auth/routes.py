from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_user_role
from app.core.db import get_db
from app.core.models import ReminderSetting, User
from app.core.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    school: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    is_admin: bool
    role: str
    school: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    role: str
    school: str


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        role=get_user_role(user),
        school=user.school or "",
    )


@router.post("/register", response_model=UserResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    username = payload.username.strip()
    email = payload.email.strip().lower()
    school = (payload.school or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="invalid username")
    if not email:
        raise HTTPException(status_code=400, detail="invalid email")

    if db.query(User).filter(func.lower(User.username) == username.lower()).first():
        raise HTTPException(status_code=400, detail="username already exists")
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=400, detail="email already exists")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        is_admin=False,
        role="student",
        school=school,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    setting = ReminderSetting(user_id=user.id, days_before=3, enabled=True)
    db.add(setting)
    db.commit()

    return _to_user_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    identifier = payload.username.strip()
    if not identifier:
        raise HTTPException(status_code=401, detail="invalid credentials")

    user = (
        db.query(User)
        .filter(
            or_(
                func.lower(User.username) == identifier.lower(),
                func.lower(User.email) == identifier.lower(),
            )
        )
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = create_access_token(user.username)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        role=get_user_role(user),
        school=user.school or "",
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(current_user)
