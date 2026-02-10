from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import (
    API_PREFIX,
    CORS_ORIGIN_REGEX,
    CORS_ORIGINS,
    ENABLE_INGEST_SCHEDULER,
    ENABLE_REMINDER_SCHEDULER,
    INGEST_INTERVAL_SECONDS,
    MODULE_PATHS,
)
from app.core.db import SessionLocal, init_db
from app.core.ingestion import ensure_default_sources
from app.core.logging import setup_logging
from app.core.module_loader import load_modules
from app.core.provider_config import ensure_provider_config_file, get_runtime_ingestion_config
from app.core.scheduler import start_ingestion_scheduler, start_reminder_scheduler
from app.core.seed import ensure_default_admin
from app.core.api.health import router as health_router


def create_app() -> FastAPI:
    setup_logging()
    ensure_provider_config_file()
    init_db()
    with SessionLocal() as db:
        ensure_default_admin(db)
        ensure_default_sources(db)

    app = FastAPI(title="SaiLi AI", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_origin_regex=CORS_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix=API_PREFIX)

    modules = load_modules(MODULE_PATHS)
    for module_def in modules:
        if module_def.router:
            app.include_router(module_def.router, prefix=API_PREFIX)

    if ENABLE_REMINDER_SCHEDULER:
        start_reminder_scheduler()
    if ENABLE_INGEST_SCHEDULER:
        ingest_cfg = get_runtime_ingestion_config()
        start_ingestion_scheduler(interval_seconds=ingest_cfg["interval_seconds"])

    return app


app = create_app()
