from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import JWT_ALGORITHM, JWT_SECRET
from app.core.db import get_db
from app.core.models import Competition, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SCHOOL_MANAGER_ROLES = {"school_admin", "student_admin"}


def get_user_role(user: User) -> str:
    if user.is_admin:
        return "platform_admin"
    role = (user.role or "student").strip().lower()
    return role or "student"


def is_platform_admin(user: User) -> bool:
    return user.is_admin or get_user_role(user) == "platform_admin"


def is_school_manager(user: User) -> bool:
    return is_platform_admin(user) or get_user_role(user) in SCHOOL_MANAGER_ROLES


def is_school_admin(user: User) -> bool:
    return is_platform_admin(user) or get_user_role(user) == "school_admin"


def require_school_scope(user: User, school: str) -> None:
    if is_platform_admin(user):
        return
    if not user.school:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="school scope required")
    if user.school != school:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cross-school access denied")


def ensure_competition_scope(user: User, competition: Competition) -> None:
    require_school_scope(user, competition.school)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid authentication",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise credentials_exception
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not is_platform_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return user


def require_platform_admin(user: User = Depends(get_current_user)) -> User:
    if not is_platform_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="platform admin only")
    return user


def require_school_manager(user: User = Depends(get_current_user)) -> User:
    if not is_school_manager(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="school manager only")
    if not user.school and not is_platform_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="school not assigned")
    return user


def require_school_admin(user: User = Depends(get_current_user)) -> User:
    if not is_school_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="school admin only")
    if not user.school and not is_platform_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="school not assigned")
    return user
