import csv
from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import (
    ensure_competition_scope,
    get_user_role,
    is_platform_admin,
    require_platform_admin,
    require_school_admin,
    require_school_manager,
)
from app.core.config import EMAIL_ENABLED
from app.core.db import get_db
from app.core.ingestion import ensure_default_sources, list_source_metrics, run_ingestion_sync
from app.core.models import Competition, CompetitionEnrollment, RecommendationRule, User
from app.core.provider_config import load_provider_config, save_provider_config
from app.core.reminders import send_due_reminders as run_due_reminders
from app.core.security import hash_password
from app.core.time import now_utc, to_naive_utc
from app.modules.competitions.schemas import (
    CompetitionCreate,
    CompetitionOut,
    CompetitionUpdate,
    tags_from_string,
    tags_to_string,
)

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_COMPETITION_LEVELS = {"national", "school"}
VALID_USER_ROLES = {"platform_admin", "school_admin", "student_admin", "student"}


class StatusUpdate(BaseModel):
    status: str


class RuleUpdate(BaseModel):
    key: str
    weight: int


class EnrollmentOut(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    status: str


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


class SchoolManagerCreatePayload(BaseModel):
    username: str
    email: str
    password: str
    role: str
    school: str


class SchoolManagerRolePayload(BaseModel):
    user_id: int
    role: str
    school: str


class SchoolManagerOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    school: str
    is_admin: bool


def _normalize_level(level: Optional[str]) -> str:
    normalized_level = (level or "national").strip().lower() or "national"
    if normalized_level not in VALID_COMPETITION_LEVELS:
        raise HTTPException(status_code=400, detail="invalid level")
    return normalized_level


def _normalize_role(role: Optional[str]) -> str:
    normalized_role = (role or "student").strip().lower() or "student"
    if normalized_role not in VALID_USER_ROLES:
        raise HTTPException(status_code=400, detail="invalid role")
    return normalized_role


def _is_school_admin_like(user: User) -> bool:
    return is_platform_admin(user) or get_user_role(user) == "school_admin"


def _ensure_competition_editable(manager: User, competition: Competition) -> None:
    ensure_competition_scope(manager, competition)
    if is_platform_admin(manager):
        return

    role = get_user_role(manager)
    if role == "school_admin":
        return

    if role == "student_admin":
        if competition.creator_user_id != manager.id:
            raise HTTPException(
                status_code=403,
                detail="student admin can only edit own uploaded competitions",
            )
        return

    raise HTTPException(status_code=403, detail="insufficient permission")


def _competition_to_out(competition: Competition) -> CompetitionOut:
    return CompetitionOut(
        id=competition.id,
        title=competition.title,
        level=competition.level,
        school=competition.school,
        description=competition.description,
        organizer=competition.organizer,
        location=competition.location,
        signup_start=competition.signup_start,
        signup_end=competition.signup_end,
        event_start=competition.event_start,
        event_end=competition.event_end,
        reward=competition.reward,
        requirements=competition.requirements,
        contact_note=competition.contact_note,
        tags=tags_from_string(competition.tags),
        status=competition.status,
        source=competition.source,
        created_at=competition.created_at,
        updated_at=competition.updated_at,
    )


@router.get("/schools/admins", response_model=list[SchoolManagerOut])
def list_school_managers(
    school: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
) -> list[SchoolManagerOut]:
    query = db.query(User).filter(User.role.in_(["school_admin", "student_admin"]))
    if school:
        query = query.filter(User.school == school.strip())
    users = query.order_by(User.school.asc(), User.username.asc()).all()
    return [
        SchoolManagerOut(
            id=item.id,
            username=item.username,
            email=item.email,
            role=item.role,
            school=item.school,
            is_admin=item.is_admin,
        )
        for item in users
    ]


@router.post("/schools/admins", response_model=SchoolManagerOut)
def create_school_manager(
    payload: SchoolManagerCreatePayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
) -> SchoolManagerOut:
    username = payload.username.strip()
    email = payload.email.strip().lower()
    school = payload.school.strip()
    role = _normalize_role(payload.role)

    if role not in {"school_admin", "student_admin"}:
        raise HTTPException(status_code=400, detail="role must be school_admin or student_admin")
    if not school:
        raise HTTPException(status_code=400, detail="school is required")

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="username already exists")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="email already exists")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        is_admin=False,
        role=role,
        school=school,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return SchoolManagerOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        school=user.school,
        is_admin=user.is_admin,
    )


@router.put("/schools/admins/role", response_model=SchoolManagerOut)
def update_school_manager_role(
    payload: SchoolManagerRolePayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
) -> SchoolManagerOut:
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    role = _normalize_role(payload.role)
    school = payload.school.strip()

    if role not in {"school_admin", "student_admin", "student"}:
        raise HTTPException(status_code=400, detail="invalid school role")
    if role in {"school_admin", "student_admin"} and not school:
        raise HTTPException(status_code=400, detail="school is required")

    user.role = role
    user.school = school
    user.is_admin = role == "platform_admin"
    db.commit()
    db.refresh(user)

    return SchoolManagerOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        school=user.school,
        is_admin=user.is_admin,
    )


@router.get("/competitions", response_model=list[CompetitionOut])
def list_competitions(
    status: Optional[str] = None,
    school: Optional[str] = None,
    db: Session = Depends(get_db),
    manager: User = Depends(require_school_manager),
) -> list[CompetitionOut]:
    query = db.query(Competition)
    if status:
        query = query.filter(Competition.status == status)

    if is_platform_admin(manager):
        if school:
            query = query.filter(Competition.school == school.strip())
    else:
        query = query.filter(Competition.school == manager.school)

    return [_competition_to_out(item) for item in query.order_by(Competition.created_at.desc()).all()]


@router.post("/competitions", response_model=CompetitionOut)
def create_competition(
    payload: CompetitionCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_school_manager),
) -> CompetitionOut:
    level = _normalize_level(payload.level)

    if not is_platform_admin(manager) and level != "school":
        raise HTTPException(status_code=403, detail="only platform admin can create national competitions")

    school = (payload.school or "").strip() or manager.school
    if is_platform_admin(manager):
        if not school:
            school = "ALL"
    else:
        school = manager.school

    competition = Competition(
        title=payload.title,
        level=level,
        school=school,
        creator_user_id=manager.id,
        description=payload.description,
        organizer=payload.organizer,
        location=payload.location,
        signup_start=to_naive_utc(payload.signup_start),
        signup_end=to_naive_utc(payload.signup_end),
        event_start=to_naive_utc(payload.event_start),
        event_end=to_naive_utc(payload.event_end),
        reward=payload.reward,
        requirements=payload.requirements,
        contact_note=(payload.contact_note or "").strip(),
        tags=tags_to_string(payload.tags),
        status="pending",
        source="manual",
    )
    db.add(competition)
    db.commit()
    db.refresh(competition)
    return _competition_to_out(competition)


@router.put("/competitions/{competition_id}", response_model=CompetitionOut)
def update_competition(
    competition_id: int,
    payload: CompetitionUpdate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_school_manager),
) -> CompetitionOut:
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="competition not found")

    _ensure_competition_editable(manager, competition)

    for field, value in payload.dict(exclude_unset=True).items():
        if field in {"signup_start", "signup_end", "event_start", "event_end"}:
            value = to_naive_utc(value)
        if field == "level" and value is not None:
            normalized_level = _normalize_level(str(value))
            if not is_platform_admin(manager) and normalized_level != "school":
                raise HTTPException(status_code=403, detail="only platform admin can set national level")
            setattr(competition, field, normalized_level)
            continue
        if field == "school" and value is not None:
            if is_platform_admin(manager):
                setattr(competition, field, str(value).strip() or competition.school)
            continue
        if field == "contact_note" and value is not None:
            setattr(competition, field, str(value).strip())
            continue
        if field == "tags" and value is not None:
            setattr(competition, field, tags_to_string(value))
        else:
            setattr(competition, field, value)

    competition.updated_at = now_utc()
    db.commit()
    db.refresh(competition)
    return _competition_to_out(competition)


@router.post("/competitions/{competition_id}/status", response_model=CompetitionOut)
def update_status(
    competition_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_school_admin),
) -> CompetitionOut:
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="competition not found")

    ensure_competition_scope(manager, competition)
    competition.status = payload.status
    competition.updated_at = now_utc()
    db.commit()
    db.refresh(competition)
    return _competition_to_out(competition)


@router.post("/competitions/{competition_id}/publish", response_model=CompetitionOut)
def publish_competition(
    competition_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_school_admin),
) -> CompetitionOut:
    return update_status(
        competition_id,
        StatusUpdate(status="published"),
        db,
        manager,
    )


@router.post("/competitions/{competition_id}/unpublish", response_model=CompetitionOut)
def unpublish_competition(
    competition_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_school_admin),
) -> CompetitionOut:
    return update_status(
        competition_id,
        StatusUpdate(status="archived"),
        db,
        manager,
    )


@router.get("/competitions/{competition_id}/registrations", response_model=list[EnrollmentOut])
def list_competition_registrations(
    competition_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_school_manager),
) -> list[EnrollmentOut]:
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="competition not found")
    ensure_competition_scope(manager, competition)

    rows = (
        db.query(CompetitionEnrollment, User)
        .join(User, User.id == CompetitionEnrollment.user_id)
        .filter(CompetitionEnrollment.competition_id == competition_id)
        .order_by(CompetitionEnrollment.id.asc())
        .all()
    )
    return [
        EnrollmentOut(
            id=enrollment.id,
            user_id=user.id,
            username=user.username,
            email=user.email,
            status=enrollment.status,
        )
        for enrollment, user in rows
    ]


@router.get("/competitions/{competition_id}/registrations/export.csv")
def export_competition_registrations_csv(
    competition_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_school_manager),
) -> Response:
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="competition not found")
    ensure_competition_scope(manager, competition)

    rows = (
        db.query(CompetitionEnrollment, User)
        .join(User, User.id == CompetitionEnrollment.user_id)
        .filter(CompetitionEnrollment.competition_id == competition_id)
        .order_by(CompetitionEnrollment.id.asc())
        .all()
    )

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["enrollment_id", "user_id", "username", "email", "status", "submitted_at"])
    for enrollment, user in rows:
        writer.writerow(
            [
                enrollment.id,
                user.id,
                user.username,
                user.email,
                enrollment.status,
                enrollment.submitted_at.isoformat() if enrollment.submitted_at else "",
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="competition-{competition_id}-registrations.csv"',
        },
    )


@router.post("/ingest/source")
def ingest_source(
    payload: Optional[IngestRequest] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
) -> dict:
    requested_source = payload.source_id if payload else None
    result = run_ingestion_sync(db, source_id=requested_source)
    if result.get("source") is None:
        raise HTTPException(status_code=400, detail="no ingestion source available")
    return result


@router.get("/ingest/sources")
def ingest_sources(
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
) -> dict:
    return {"items": list_source_metrics(db)}


@router.get("/config/api-providers")
def get_api_providers(
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
) -> dict:
    return load_provider_config(mask_secrets=True)


@router.put("/config/api-providers")
def put_api_providers(
    payload: ApiProvidersPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
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
    admin: User = Depends(require_platform_admin),
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
    admin: User = Depends(require_platform_admin),
) -> dict:
    if not EMAIL_ENABLED:
        raise HTTPException(status_code=400, detail="email not configured")
    sent = run_due_reminders(db)
    return {"sent": sent}
