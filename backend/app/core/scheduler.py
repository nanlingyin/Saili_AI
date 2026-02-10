import logging
import threading
import time

from app.core.config import EMAIL_ENABLED
from app.core.db import SessionLocal
from app.core.ingestion import run_ingestion_sync
from app.core.reminders import send_due_reminders

logger = logging.getLogger(__name__)


def start_reminder_scheduler(interval_seconds: int = 3600) -> None:
    def loop() -> None:
        while True:
            if EMAIL_ENABLED:
                try:
                    with SessionLocal() as db:
                        sent = send_due_reminders(db)
                        logger.info("reminder job sent %s emails", sent)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("reminder job failed: %s", exc)
            else:
                logger.info("reminder job skipped: email not configured")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()


def start_ingestion_scheduler(interval_seconds: int = 900) -> None:
    def loop() -> None:
        while True:
            try:
                with SessionLocal() as db:
                    result = run_ingestion_sync(db)
                    logger.info(
                        "ingestion job source=%s processed=%s created=%s updated=%s skipped=%s",
                        result.get("source"),
                        result.get("processed"),
                        result.get("created"),
                        result.get("updated"),
                        result.get("skipped"),
                    )
            except Exception as exc:  # noqa: BLE001
                logger.exception("ingestion job failed: %s", exc)
            time.sleep(interval_seconds)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
