from sqlalchemy.orm import Session

from app.core.config import DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME
from app.core.models import User
from app.core.security import hash_password


def ensure_default_admin(db: Session) -> None:
    existing = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
    if existing:
        changed = False
        if not existing.is_admin:
            existing.is_admin = True
            changed = True
        if (existing.role or "").strip().lower() != "platform_admin":
            existing.role = "platform_admin"
            changed = True
        if existing.school is None:
            existing.school = ""
            changed = True
        if changed:
            db.commit()
        return

    admin = User(
        username=DEFAULT_ADMIN_USERNAME,
        email=DEFAULT_ADMIN_EMAIL,
        password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
        is_admin=True,
        role="platform_admin",
        school="",
    )
    db.add(admin)
    db.commit()
