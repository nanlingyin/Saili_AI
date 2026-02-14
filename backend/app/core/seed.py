import json
import logging
import os
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import (
    COMPETITIONS_SEED_PATH,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
)
from app.core.models import Competition, User
from app.core.security import hash_password

logger = logging.getLogger(__name__)


def _normalize_url(url: str | None) -> str:
    if not url:
        return ""
    value = url.strip()
    if not value or value.startswith("微信公众号"):
        return ""
    if not re.match(r"^https?://", value, re.IGNORECASE):
        value = f"https://{value}"
    return value


def ensure_default_admin(db: Session) -> None:
    existing = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
    if existing:
        return

    admin = User(
        username=DEFAULT_ADMIN_USERNAME,
        email=DEFAULT_ADMIN_EMAIL,
        password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
        is_admin=True,
    )
    db.add(admin)
    db.commit()


def seed_competitions(db: Session) -> int:
    """从 competitions_seed.json 导入竞赛种子数据，返回新增数量。"""
    if os.environ.get("SKIP_SEED", "").strip() in ("1", "true", "yes"):
        return 0

    path = Path(COMPETITIONS_SEED_PATH)
    if not path.exists():
        logger.warning("seed file not found: %s", path)
        return 0

    with path.open("r", encoding="utf-8-sig") as f:
        seed_data = json.load(f)

    created = 0
    for item in seed_data:
        seed_id = item.get("id")
        name = (item.get("name") or "").strip()
        if not name:
            continue

        external_id = f"seed:{seed_id}"
        exists = db.query(Competition).filter(Competition.external_id == external_id).first()
        if exists:
            continue

        url = _normalize_url(item.get("url"))
        comp = Competition(
            external_id=external_id,
            source="seed",
            title=name,
            url=url,
            description=(item.get("description") or "").strip(),
            status="published",
            crawl_status="待确认",
        )
        db.add(comp)
        created += 1

    if created:
        db.commit()
        logger.info("seeded %d competitions from %s", created, path)
    return created
