import os
from pathlib import Path

API_PREFIX = "/api/v1"
MODULE_PATHS = [
    "app.modules.auth.module",
    "app.modules.competitions.module",
    "app.modules.teams.module",
    "app.modules.resume.module",
    "app.modules.favorites.module",
    "app.modules.reminders.module",
    "app.modules.recommendations.module",
    "app.modules.profile.module",
    "app.modules.admin.module",
    "app.modules.sample.module",
    "app.modules.forum.module",
]

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _resolve_backend_path(path_value: str) -> str:
    path = Path(path_value)
    if path.is_absolute():
        return str(path)
    return str((BACKEND_DIR / path).resolve())


def _normalize_database_url(db_url: str) -> str:
    if not db_url.startswith("sqlite:///"):
        return db_url

    sqlite_path = db_url.replace("sqlite:///", "", 1)
    if sqlite_path == ":memory:":
        return db_url

    path = Path(sqlite_path)
    if path.is_absolute():
        return db_url
    return f"sqlite:///{_resolve_backend_path(sqlite_path)}"


DATABASE_URL = _normalize_database_url(
    os.getenv("DATABASE_URL", f"sqlite:///{_resolve_backend_path('data/app.db')}")
)

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "")
EMAIL_ENABLED = all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM])
ENABLE_REMINDER_SCHEDULER = (
    os.getenv("ENABLE_REMINDER_SCHEDULER", "true").lower() == "true"
)
ENABLE_INGEST_SCHEDULER = (
    os.getenv("ENABLE_INGEST_SCHEDULER", "false").lower() == "true"
)
INGEST_INTERVAL_SECONDS = int(os.getenv("INGEST_INTERVAL_SECONDS", "900"))

STABLE_SOURCE_PATH = _resolve_backend_path(
    os.getenv("STABLE_SOURCE_PATH", "data/competition_source.json")
)
FALLBACK_SOURCE_PATH = _resolve_backend_path(
    os.getenv("FALLBACK_SOURCE_PATH", "data/competition_fallback.json")
)
INGEST_FAILURE_THRESHOLD = int(os.getenv("INGEST_FAILURE_THRESHOLD", "3"))

AI_API_BASE_URL = os.getenv("AI_API_BASE_URL", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_API_MODEL = os.getenv("AI_API_MODEL", "")
AI_API_TIMEOUT_SECONDS = int(os.getenv("AI_API_TIMEOUT_SECONDS", "15"))
AI_ENABLED = bool(AI_API_BASE_URL and AI_API_KEY and AI_API_MODEL)

_cors_origins_env = os.getenv("CORS_ORIGINS", "")
if _cors_origins_env.strip():
    CORS_ORIGINS = [item.strip() for item in _cors_origins_env.split(",") if item.strip()]
else:
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:5173",
    ]

CORS_ORIGIN_REGEX = os.getenv(
    "CORS_ORIGIN_REGEX",
    r"^https?://([A-Za-z0-9\.-]+|(\d{1,3}\.){3}\d{1,3})(:\d+)?$",
)

API_PROVIDER_CONFIG_PATH = os.getenv(
    "API_PROVIDER_CONFIG_PATH",
    _resolve_backend_path("config/api_providers.yaml"),
)
API_PROVIDER_CONFIG_PATH = _resolve_backend_path(API_PROVIDER_CONFIG_PATH)
