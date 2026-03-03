import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL


connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _sqlite_column_exists(conn, table_name: str, column_name: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return any(row[1] == column_name for row in rows)


def _sqlite_apply_compat_migrations() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as conn:
        if not _sqlite_column_exists(conn, "users", "kicked_count"):
            conn.execute(text("ALTER TABLE users ADD COLUMN kicked_count INTEGER DEFAULT 0 NOT NULL"))
        if not _sqlite_column_exists(conn, "users", "missed_checkins"):
            conn.execute(text("ALTER TABLE users ADD COLUMN missed_checkins INTEGER DEFAULT 0 NOT NULL"))
        if not _sqlite_column_exists(conn, "users", "completed_tasks"):
            conn.execute(text("ALTER TABLE users ADD COLUMN completed_tasks INTEGER DEFAULT 0 NOT NULL"))
        if not _sqlite_column_exists(conn, "users", "role"):
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(30) DEFAULT 'student' NOT NULL"))
        if not _sqlite_column_exists(conn, "users", "school"):
            conn.execute(text("ALTER TABLE users ADD COLUMN school VARCHAR(255) DEFAULT '' NOT NULL"))
        if not _sqlite_column_exists(conn, "competitions", "school"):
            conn.execute(text("ALTER TABLE competitions ADD COLUMN school VARCHAR(255) DEFAULT 'ALL' NOT NULL"))
        if not _sqlite_column_exists(conn, "competitions", "level"):
            conn.execute(text("ALTER TABLE competitions ADD COLUMN level VARCHAR(20) DEFAULT 'national' NOT NULL"))
        if not _sqlite_column_exists(conn, "competitions", "creator_user_id"):
            conn.execute(text("ALTER TABLE competitions ADD COLUMN creator_user_id INTEGER"))
        if not _sqlite_column_exists(conn, "competitions", "contact_note"):
            conn.execute(text("ALTER TABLE competitions ADD COLUMN contact_note VARCHAR(255) DEFAULT '' NOT NULL"))


def init_db() -> None:
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    from app.core import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _sqlite_apply_compat_migrations()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
