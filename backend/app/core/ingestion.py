import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.models import (
    Competition,
    CompetitionSourceLink,
    IngestionRawItem,
    IngestionSource,
)
from app.core.provider_config import (
    get_runtime_ai_config,
    get_runtime_ingestion_config,
)
from app.core.time import now_utc, to_naive_utc
from app.modules.competitions.schemas import tags_to_string

logger = logging.getLogger(__name__)

PARSER_VERSION = "v1"
EXTRACTOR_RULES_VERSION = "rules-v1"
EXTRACTOR_AI_VERSION = "ai-v1"
SOURCE_TYPE_STABLE_FILE = "stable_file"
SOURCE_TYPE_FALLBACK_FILE = "fallback_file"


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return to_naive_utc(value)
    if not isinstance(value, str):
        return None
    try:
        return to_naive_utc(datetime.fromisoformat(value))
    except ValueError:
        return None


def _checksum(item: dict[str, Any]) -> str:
    text = json.dumps(item, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _extract_tags(raw: dict[str, Any], text: str) -> list[str]:
    tags = raw.get("tags")
    if isinstance(tags, list):
        return [str(tag).strip() for tag in tags if str(tag).strip()]
    matched = []
    for token in ("英语", "编程", "数学", "AI", "艺术", "体育"):
        if token.lower() in text.lower():
            matched.append(token)
    return matched


def _fallback_extract(raw: dict[str, Any]) -> tuple[dict[str, Any], str]:
    text = " ".join(
        str(raw.get(key, "") or "")
        for key in ("title", "description", "requirements", "organizer")
    ).strip()
    title = (raw.get("title") or "").strip()
    signup_end = _parse_datetime(raw.get("signup_end"))
    if not signup_end:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if match:
            signup_end = _parse_datetime(match.group(1))

    extracted = {
        "title": title,
        "level": raw.get("level") or "national",
        "description": raw.get("description"),
        "organizer": raw.get("organizer"),
        "location": raw.get("location"),
        "signup_start": _parse_datetime(raw.get("signup_start")),
        "signup_end": signup_end,
        "event_start": _parse_datetime(raw.get("event_start")),
        "event_end": _parse_datetime(raw.get("event_end")),
        "reward": raw.get("reward"),
        "requirements": raw.get("requirements"),
        "tags": _extract_tags(raw, text),
        "status": raw.get("status") or "pending",
    }
    return extracted, EXTRACTOR_RULES_VERSION


def _ai_extract(raw: dict[str, Any], ai_cfg: Optional[dict[str, Any]] = None) -> tuple[dict[str, Any], str]:
    ai_cfg = ai_cfg or get_runtime_ai_config()
    if not ai_cfg["enabled"]:
        return _fallback_extract(raw)

    payload = {
        "model": ai_cfg["model"],
        "input": raw,
        "schema": [
            "title",
            "description",
            "organizer",
            "location",
            "signup_start",
            "signup_end",
            "event_start",
            "event_end",
            "reward",
            "requirements",
            "tags",
            "status",
        ],
    }
    headers = {"Authorization": f"Bearer {ai_cfg['api_key']}"}
    try:
        with httpx.Client(timeout=ai_cfg["timeout_seconds"]) as client:
            response = client.post(ai_cfg["base_url"], json=payload, headers=headers)
            response.raise_for_status()
        data = response.json()
        extracted = data.get("output", data)
        if not isinstance(extracted, dict):
            raise ValueError("invalid ai response")
        fallback, _ = _fallback_extract(raw)
        fallback.update(extracted)
        fallback["signup_start"] = _parse_datetime(fallback.get("signup_start"))
        fallback["signup_end"] = _parse_datetime(fallback.get("signup_end"))
        fallback["event_start"] = _parse_datetime(fallback.get("event_start"))
        fallback["event_end"] = _parse_datetime(fallback.get("event_end"))
        if not isinstance(fallback.get("tags"), list):
            fallback["tags"] = _extract_tags(raw, " ".join(str(v) for v in raw.values()))
        return fallback, EXTRACTOR_AI_VERSION
    except Exception as exc:  # noqa: BLE001
        logger.warning("ai extraction failed, fallback to rules: %s", exc)
        return _fallback_extract(raw)


def ensure_default_sources(db: Session) -> None:
    ingestion_cfg = get_runtime_ingestion_config()
    defaults = [
        {
            "source_id": "stable_primary",
            "source_type": SOURCE_TYPE_STABLE_FILE,
            "config_json": json.dumps(
                {"path": ingestion_cfg["stable_source_path"]},
                ensure_ascii=False,
            ),
            "priority": 10,
            "failure_threshold": ingestion_cfg["failure_threshold"],
        },
        {
            "source_id": "fallback_file",
            "source_type": SOURCE_TYPE_FALLBACK_FILE,
            "config_json": json.dumps(
                {"path": ingestion_cfg["fallback_source_path"]},
                ensure_ascii=False,
            ),
            "priority": 50,
            "failure_threshold": ingestion_cfg["failure_threshold"],
        },
    ]
    changed = False
    for item in defaults:
        exists = (
            db.query(IngestionSource)
            .filter(IngestionSource.source_id == item["source_id"])
            .first()
        )
        if exists:
            if exists.config_json != item["config_json"]:
                exists.config_json = item["config_json"]
                changed = True
            if exists.failure_threshold != item["failure_threshold"]:
                exists.failure_threshold = item["failure_threshold"]
                changed = True
            continue
        db.add(IngestionSource(**item))
        changed = True
    if changed:
        db.commit()


def _load_file_source(source: IngestionSource) -> list[dict[str, Any]]:
    ingestion_cfg = get_runtime_ingestion_config()
    config = json.loads(source.config_json or "{}")
    default_path = (
        ingestion_cfg["stable_source_path"]
        if source.source_id == "stable_primary"
        else ingestion_cfg["fallback_source_path"]
    )
    path = Path(config.get("path") or default_path)
    if not path.exists():
        raise FileNotFoundError(f"source file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("source payload must be a list")
    return payload


def _select_active_source(db: Session) -> Optional[IngestionSource]:
    sources = (
        db.query(IngestionSource)
        .filter(IngestionSource.enabled.is_(True))
        .order_by(IngestionSource.priority.asc())
        .all()
    )
    if not sources:
        return None
    for source in sources:
        if source.health_status != "degraded":
            return source
    return sources[0]


def _find_competition_for_item(
    db: Session,
    source_id: str,
    source_item_id: str,
    extracted: dict[str, Any],
) -> Optional[Competition]:
    link = (
        db.query(CompetitionSourceLink)
        .filter(
            CompetitionSourceLink.source_id == source_id,
            CompetitionSourceLink.source_item_id == source_item_id,
        )
        .first()
    )
    if link:
        return (
            db.query(Competition)
            .filter(Competition.id == link.competition_id)
            .first()
        )

    title = (extracted.get("title") or "").strip()
    signup_end = extracted.get("signup_end")
    if title and signup_end:
        return (
            db.query(Competition)
            .filter(
                Competition.title == title,
                Competition.signup_end == signup_end,
            )
            .first()
        )
    return None


def _save_raw_item(
    db: Session,
    source_id: str,
    source_item_id: str,
    source_url: Optional[str],
    raw_item: dict[str, Any],
    payload_checksum: str,
    extracted: dict[str, Any],
    extraction_status: str,
    extractor_version: str,
) -> None:
    raw_record = (
        db.query(IngestionRawItem)
        .filter(
            IngestionRawItem.source_id == source_id,
            IngestionRawItem.source_item_id == source_item_id,
        )
        .first()
    )
    if not raw_record:
        raw_record = IngestionRawItem(
            source_id=source_id,
            source_item_id=source_item_id,
            source_url=source_url,
            payload_json=json.dumps(raw_item, ensure_ascii=False),
            payload_checksum=payload_checksum,
        )
        db.add(raw_record)

    raw_record.source_url = source_url
    raw_record.payload_json = json.dumps(raw_item, ensure_ascii=False)
    raw_record.payload_checksum = payload_checksum
    raw_record.extracted_json = json.dumps(extracted, ensure_ascii=False, default=str)
    raw_record.extraction_status = extraction_status
    raw_record.parser_version = PARSER_VERSION
    raw_record.extractor_version = extractor_version
    raw_record.fetched_at = now_utc()
    raw_record.updated_at = now_utc()


def _upsert_competition(
    db: Session,
    source: IngestionSource,
    source_item_id: str,
    source_url: Optional[str],
    extracted: dict[str, Any],
    extractor_version: str,
) -> tuple[bool, bool]:
    competition = _find_competition_for_item(db, source.source_id, source_item_id, extracted)
    created = False
    if not competition:
        competition = Competition(
            external_id=f"{source.source_id}:{source_item_id}",
            source=source.source_id,
            title=extracted["title"],
            level=(extracted.get("level") or "national"),
            status=extracted.get("status") or "pending",
        )
        db.add(competition)
        created = True

    competition.source = source.source_id
    competition.title = extracted["title"]
    competition.level = extracted.get("level") or competition.level or "national"
    competition.description = extracted.get("description")
    competition.organizer = extracted.get("organizer")
    competition.location = extracted.get("location")
    competition.signup_start = extracted.get("signup_start")
    competition.signup_end = extracted.get("signup_end")
    competition.event_start = extracted.get("event_start")
    competition.event_end = extracted.get("event_end")
    competition.reward = extracted.get("reward")
    competition.requirements = extracted.get("requirements")
    competition.tags = tags_to_string(extracted.get("tags", []))
    competition.status = extracted.get("status") or "pending"
    competition.updated_at = now_utc()

    db.flush()

    link = (
        db.query(CompetitionSourceLink)
        .filter(
            CompetitionSourceLink.source_id == source.source_id,
            CompetitionSourceLink.source_item_id == source_item_id,
        )
        .first()
    )
    if not link:
        link = CompetitionSourceLink(
            competition_id=competition.id,
            source_id=source.source_id,
            source_item_id=source_item_id,
        )
        db.add(link)
    link.competition_id = competition.id
    link.source_url = source_url
    link.parser_version = PARSER_VERSION
    link.extractor_version = extractor_version
    link.fetched_at = now_utc()
    link.updated_at = now_utc()
    return created, not created


def run_ingestion_sync(
    db: Session,
    source_id: Optional[str] = None,
) -> dict[str, Any]:
    ensure_default_sources(db)
    source: Optional[IngestionSource]
    if source_id:
        source = (
            db.query(IngestionSource)
            .filter(IngestionSource.source_id == source_id, IngestionSource.enabled.is_(True))
            .first()
        )
    else:
        source = _select_active_source(db)
    if not source:
        return {"processed": 0, "created": 0, "updated": 0, "skipped": 0, "source": None}

    source.total_runs += 1
    started = now_utc()
    created = 0
    updated = 0
    skipped = 0
    parse_errors = 0
    processed = 0
    fallback_used = False
    degraded_from: Optional[str] = None
    ai_cfg = get_runtime_ai_config()

    try:
        items = _load_file_source(source)
    except Exception as exc:  # noqa: BLE001
        source.failure_count += 1
        source.failure_runs += 1
        source.last_error = str(exc)
        source.health_status = (
            "degraded" if source.failure_count >= source.failure_threshold else "warning"
        )
        fallback = (
            db.query(IngestionSource)
            .filter(
                IngestionSource.enabled.is_(True),
                IngestionSource.source_id != source.source_id,
            )
            .order_by(IngestionSource.priority.asc())
            .first()
        )
        if not fallback:
            db.commit()
            raise
        fallback_used = True
        degraded_from = source.source_id
        source = fallback
        source.total_runs += 1
        items = _load_file_source(source)

    for item in items:
        raw_item = item if isinstance(item, dict) else {}
        raw_source_item_id = raw_item.get("source_item_id") or raw_item.get("external_id")
        source_item_id = str(raw_source_item_id or "").strip()
        if not source_item_id:
            skipped += 1
            continue

        checksum = _checksum(raw_item)
        raw_record = (
            db.query(IngestionRawItem)
            .filter(
                IngestionRawItem.source_id == source.source_id,
                IngestionRawItem.source_item_id == source_item_id,
            )
            .first()
        )
        if raw_record and raw_record.payload_checksum == checksum:
            skipped += 1
            continue

        extracted, extractor_version = _ai_extract(raw_item, ai_cfg=ai_cfg)
        extracted["title"] = (extracted.get("title") or "").strip()
        extracted["signup_start"] = _parse_datetime(extracted.get("signup_start"))
        extracted["signup_end"] = _parse_datetime(extracted.get("signup_end"))
        extracted["event_start"] = _parse_datetime(extracted.get("event_start"))
        extracted["event_end"] = _parse_datetime(extracted.get("event_end"))

        source_url = raw_item.get("source_url")
        if not extracted["title"]:
            parse_errors += 1
            _save_raw_item(
                db,
                source.source_id,
                source_item_id,
                source_url,
                raw_item,
                checksum,
                extracted,
                "needs_review",
                extractor_version,
            )
            continue

        created_flag, updated_flag = _upsert_competition(
            db,
            source,
            source_item_id,
            source_url,
            extracted,
            extractor_version,
        )
        if created_flag:
            created += 1
        if updated_flag:
            updated += 1
        processed += 1

        extraction_status = "ok"
        if not extracted.get("signup_end"):
            extraction_status = "needs_review"
            parse_errors += 1

        _save_raw_item(
            db,
            source.source_id,
            source_item_id,
            source_url,
            raw_item,
            checksum,
            extracted,
            extraction_status,
            extractor_version,
        )

    source.last_sync_at = started
    source.last_success_at = now_utc()
    source.success_runs += 1
    source.failure_count = 0
    source.health_status = "healthy"
    source.last_error = None
    source.parse_error_count += parse_errors
    source.freshness_hours = 0.0

    db.commit()
    return {
        "source": source.source_id,
        "processed": processed,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "parse_errors": parse_errors,
        "fallback_used": fallback_used,
        "degraded_from": degraded_from,
    }


def list_source_metrics(db: Session) -> list[dict[str, Any]]:
    ensure_default_sources(db)
    rows = db.query(IngestionSource).order_by(IngestionSource.priority.asc()).all()
    now = now_utc()
    result: list[dict[str, Any]] = []
    for row in rows:
        total = row.total_runs or 0
        success = row.success_runs or 0
        success_rate = (success / total) if total else 0.0
        freshness_hours = None
        if row.last_success_at:
            freshness_hours = round(
                (now - row.last_success_at).total_seconds() / 3600,
                2,
            )
            row.freshness_hours = freshness_hours

        result.append(
            {
                "source_id": row.source_id,
                "source_type": row.source_type,
                "priority": row.priority,
                "enabled": row.enabled,
                "health_status": row.health_status,
                "failure_count": row.failure_count,
                "failure_threshold": row.failure_threshold,
                "last_sync_at": row.last_sync_at,
                "last_success_at": row.last_success_at,
                "last_error": row.last_error,
                "total_runs": total,
                "success_runs": success,
                "failure_runs": row.failure_runs or 0,
                "parse_error_count": row.parse_error_count or 0,
                "success_rate": round(success_rate, 4),
                "freshness_hours": freshness_hours,
            }
        )
    db.commit()
    return result
