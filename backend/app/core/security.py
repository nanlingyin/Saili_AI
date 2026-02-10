from datetime import timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import JWT_ALGORITHM, JWT_SECRET
from app.core.provider_config import get_runtime_auth_config
from app.core.time import now_utc

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    auth_cfg = get_runtime_auth_config()
    expire = now_utc() + timedelta(minutes=auth_cfg["access_token_expire_minutes"])
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
