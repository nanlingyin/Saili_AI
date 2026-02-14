import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL


connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _ensure_sqlite_competition_columns() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    expected = {
        "url": "VARCHAR(500) DEFAULT ''",
        "crawl_status": "VARCHAR(20) DEFAULT ''",
        "crawl_error": "TEXT DEFAULT ''",
        "source_title": "VARCHAR(255) DEFAULT ''",
        "last_crawled": "DATETIME",
    }
    with engine.begin() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(competitions)").fetchall()
        if not rows:
            return
        existing = {row[1] for row in rows}
        for column, ddl in expected.items():
            if column not in existing:
                conn.exec_driver_sql(
                    f"ALTER TABLE competitions ADD COLUMN {column} {ddl}"
                )


def init_db() -> None:
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    from app.core import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_competition_columns()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
