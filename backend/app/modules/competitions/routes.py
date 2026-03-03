from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import not_, or_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.models import Competition, CompetitionEnrollment, User
from app.core.time import now_utc
from app.modules.competitions.schemas import (
    CompetitionListResponse,
    CompetitionOut,
    tags_from_string,
)

router = APIRouter(prefix="/competitions", tags=["competitions"])

HIGH_VALUE_KEYWORDS = ["互联网+", "挑战杯", "三创", "大英赛", "数学建模", "ACM"]
LOW_VALUE_KEYWORDS = ["水赛", "不知名", "凑学分", "培训证书", "打卡活动"]


def _build_keyword_clause(keywords: list[str]):
    clauses = []
    for keyword in keywords:
        like = f"%{keyword}%"
        clauses.extend(
            [
                Competition.title.ilike(like),
                Competition.description.ilike(like),
                Competition.tags.ilike(like),
            ]
        )
    return or_(*clauses) if clauses else None


def to_out(competition: Competition) -> CompetitionOut:
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


@router.get("", response_model=CompetitionListResponse)
def list_competitions(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    tag: Optional[str] = None,
    level: Optional[str] = None,
    goal: Optional[str] = None,
    hide_low_value: bool = False,
    sort: str = "deadline",
    order: str = "asc",
    page: int = 1,
    page_size: int = 20,
) -> CompetitionListResponse:
    query = db.query(Competition).filter(Competition.status == "published")

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100
    if sort not in {"deadline", "created"}:
        sort = "deadline"
    if order not in {"asc", "desc"}:
        order = "asc"

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Competition.title.ilike(like),
                Competition.description.ilike(like),
                Competition.organizer.ilike(like),
            )
        )

    if tag:
        query = query.filter(Competition.tags.ilike(f"%{tag}%"))

    if level:
        normalized_level = level.strip().lower()
        if normalized_level in {"national", "school"}:
            query = query.filter(Competition.level == normalized_level)

    if goal == "保研加分":
        clause = _build_keyword_clause(HIGH_VALUE_KEYWORDS)
        if clause is not None:
            query = query.filter(clause)

    if hide_low_value:
        clause = _build_keyword_clause(LOW_VALUE_KEYWORDS)
        if clause is not None:
            query = query.filter(not_(clause))

    if sort == "created":
        order_by = Competition.created_at
    else:
        order_by = Competition.signup_end

    if order == "desc":
        order_by = order_by.desc()

    total = query.count()
    items = (
        query.order_by(order_by)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return CompetitionListResponse(
        items=[to_out(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/school/current", response_model=list[CompetitionOut])
def list_school_current_competitions(
    school: str,
    db: Session = Depends(get_db),
) -> list[CompetitionOut]:
    now = now_utc()
    items = (
        db.query(Competition)
        .filter(
            Competition.status == "published",
            or_(Competition.school == school, Competition.school == "ALL", Competition.school == ""),
            or_(Competition.signup_end.is_(None), Competition.signup_end >= now),
        )
        .order_by(Competition.signup_end.asc())
        .all()
    )
    return [to_out(item) for item in items]


@router.post("/{competition_id}/enroll")
def enroll_competition(
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition or competition.status != "published":
        raise HTTPException(status_code=404, detail="competition not found")

    existing = (
        db.query(CompetitionEnrollment)
        .filter(
            CompetitionEnrollment.competition_id == competition_id,
            CompetitionEnrollment.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        return {"status": existing.status}

    enrollment = CompetitionEnrollment(
        competition_id=competition_id,
        user_id=current_user.id,
        status="registered",
    )
    db.add(enrollment)
    db.commit()
    return {"status": "registered"}


@router.post("/{competition_id}/submit")
def submit_competition(
    competition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    enrollment = (
        db.query(CompetitionEnrollment)
        .filter(
            CompetitionEnrollment.competition_id == competition_id,
            CompetitionEnrollment.user_id == current_user.id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=400, detail="please enroll first")

    enrollment.status = "submitted"
    enrollment.submitted_at = now_utc()
    db.commit()
    return {"status": "submitted"}


@router.get("/{competition_id}", response_model=CompetitionOut)
def get_competition(
    competition_id: int,
    db: Session = Depends(get_db),
) -> CompetitionOut:
    competition = (
        db.query(Competition)
        .filter(Competition.id == competition_id, Competition.status == "published")
        .first()
    )
    if not competition:
        raise HTTPException(status_code=404, detail="competition not found")
    return to_out(competition)
