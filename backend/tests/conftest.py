import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
TEST_DB_PATH = DATA_DIR / f"test-{uuid.uuid4().hex}.db"
TEST_SOURCE_PATH = DATA_DIR / f"source-{uuid.uuid4().hex}.json"
TEST_FALLBACK_SOURCE_PATH = DATA_DIR / f"fallback-{uuid.uuid4().hex}.json"
TEST_PROVIDER_CONFIG_PATH = DATA_DIR / f"provider-config-{uuid.uuid4().hex}.yaml"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["ENABLE_REMINDER_SCHEDULER"] = "false"
os.environ["ENABLE_INGEST_SCHEDULER"] = "false"
os.environ["SKIP_SEED"] = "1"
os.environ["STABLE_SOURCE_PATH"] = TEST_SOURCE_PATH.as_posix()
os.environ["FALLBACK_SOURCE_PATH"] = TEST_FALLBACK_SOURCE_PATH.as_posix()
os.environ["API_PROVIDER_CONFIG_PATH"] = TEST_PROVIDER_CONFIG_PATH.as_posix()

TEST_SOURCE_PATH.write_text("[]", encoding="utf-8")
TEST_FALLBACK_SOURCE_PATH.write_text("[]", encoding="utf-8")

from app.core import models  # noqa: F401,E402
from app.core.db import Base, engine  # noqa: E402
from app.main import create_app  # noqa: E402


def reset_database() -> None:
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    if TEST_PROVIDER_CONFIG_PATH.exists():
        TEST_PROVIDER_CONFIG_PATH.unlink()


@pytest.fixture()
def client():
    reset_database()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
