from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.config import EMAIL_ENABLED
from app.core.db import get_db
from app.core.ingestion import ensure_default_sources, list_source_metrics, run_ingestion_sync
from app.core.models import Competition, RecommendationRule, User
from app.core.provider_config import load_provider_config, save_provider_config
from app.core.reminders import send_due_reminders as run_due_reminders
from app.core.time import now_utc, to_naive_utc
from app.modules.competitions.schemas import (
    CompetitionCreate,
    CompetitionOut,
    CompetitionUpdate,
    tags_from_string,
    tags_to_string,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class StatusUpdate(BaseModel):
    status: str


class RuleUpdate(BaseModel):
    key: str
    weight: int


class IngestRequest(BaseModel):
    source_id: Optional[str] = None


class AiExtractionConfigPayload(BaseModel):
    enabled: bool
    base_url: str
    model: str
    api_key: str = ""
    timeout_seconds: int = 15


class IngestionConfigPayload(BaseModel):
    stable_source_path: str
    fallback_source_path: str
    failure_threshold: int = 3
    interval_seconds: int = 900


class AuthConfigPayload(BaseModel):
    access_token_expire_minutes: int


class ApiProvidersPayload(BaseModel):
    version: int = 1
    providers: dict


def to_out(competition: Competition) -> CompetitionOut:
    return CompetitionOut(
        id=competition.id,
        title=competition.title,
        description=competition.description,
        organizer=competition.organizer,
        location=competition.location,
        signup_start=competition.signup_start,
        signup_end=competition.signup_end,
        event_start=competition.event_start,
        event_end=competition.event_end,
        reward=competition.reward,
        requirements=competition.requirements,
        tags=tags_from_string(competition.tags),
        status=competition.status,
        source=competition.source,
        created_at=competition.created_at,
        updated_at=competition.updated_at,
    )


@router.get("/competitions", response_model=list[CompetitionOut])
def list_competitions(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[CompetitionOut]:
    query = db.query(Competition)
    if status:
        query = query.filter(Competition.status == status)
    return [to_out(item) for item in query.order_by(Competition.created_at.desc()).all()]


@router.post("/competitions", response_model=CompetitionOut)
def create_competition(
    payload: CompetitionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> CompetitionOut:
    competition = Competition(
        title=payload.title,
        description=payload.description,
        organizer=payload.organizer,
        location=payload.location,
        signup_start=to_naive_utc(payload.signup_start),
        signup_end=to_naive_utc(payload.signup_end),
        event_start=to_naive_utc(payload.event_start),
        event_end=to_naive_utc(payload.event_end),
        reward=payload.reward,
        requirements=payload.requirements,
        tags=tags_to_string(payload.tags),
        status="pending",
        source="manual",
    )
    db.add(competition)
    db.commit()
    db.refresh(competition)
    return to_out(competition)


@router.put("/competitions/{competition_id}", response_model=CompetitionOut)
def update_competition(
    competition_id: int,
    payload: CompetitionUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> CompetitionOut:
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="competition not found")

    for field, value in payload.dict(exclude_unset=True).items():
        if field in {"signup_start", "signup_end", "event_start", "event_end"}:
            value = to_naive_utc(value)
        if field == "tags" and value is not None:
            setattr(competition, field, tags_to_string(value))
        else:
            setattr(competition, field, value)

    competition.updated_at = now_utc()
    db.commit()
    db.refresh(competition)
    return to_out(competition)


@router.post("/competitions/{competition_id}/status", response_model=CompetitionOut)
def update_status(
    competition_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> CompetitionOut:
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="competition not found")

    competition.status = payload.status
    competition.updated_at = now_utc()
    db.commit()
    db.refresh(competition)
    return to_out(competition)


@router.post("/competitions/{competition_id}/publish", response_model=CompetitionOut)
def publish_competition(
    competition_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> CompetitionOut:
    return update_status(
        competition_id,
        StatusUpdate(status="published"),
        db,
        admin,
    )


@router.post("/competitions/{competition_id}/unpublish", response_model=CompetitionOut)
def unpublish_competition(
    competition_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> CompetitionOut:
    return update_status(
        competition_id,
        StatusUpdate(status="archived"),
        db,
        admin,
    )


@router.post("/ingest/source")
def ingest_source(
    payload: Optional[IngestRequest] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    requested_source = payload.source_id if payload else None
    result = run_ingestion_sync(db, source_id=requested_source)
    if result.get("source") is None:
        raise HTTPException(status_code=400, detail="no ingestion source available")
    return result


@router.get("/ingest/sources")
def ingest_sources(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    return {"items": list_source_metrics(db)}


@router.get("/config/api-providers")
def get_api_providers(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    return load_provider_config(mask_secrets=True)


@router.put("/config/api-providers")
def put_api_providers(
    payload: ApiProvidersPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    providers = payload.providers or {}
    ai = providers.get("ai_extraction", {})
    ingestion = providers.get("ingestion", {})
    auth = providers.get("auth", {})

    validated = {
        "version": payload.version,
        "providers": {
            "ai_extraction": AiExtractionConfigPayload(**ai).model_dump(),
            "ingestion": IngestionConfigPayload(**ingestion).model_dump(),
            "auth": AuthConfigPayload(**auth).model_dump(),
        },
    }
    saved = save_provider_config(validated)
    ensure_default_sources(db)
    return saved


@router.put("/recommendation-rules")
def update_rules(
    payload: list[RuleUpdate],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    for rule in payload:
        existing = db.query(RecommendationRule).filter(RecommendationRule.key == rule.key).first()
        if existing:
            existing.weight = rule.weight
            existing.updated_at = now_utc()
        else:
            db.add(RecommendationRule(key=rule.key, weight=rule.weight))
    db.commit()
    return {"status": "ok"}


@router.post("/reminders/send")
def send_due_reminders(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    if not EMAIL_ENABLED:
        raise HTTPException(status_code=400, detail="email not configured")
    sent = run_due_reminders(db)
    return {"sent": sent}
