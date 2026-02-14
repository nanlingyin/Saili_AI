from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import Competition
from app.modules.competitions.schemas import (
    CompetitionListResponse,
    CompetitionOut,
    tags_from_string,
)

router = APIRouter(prefix="/competitions", tags=["competitions"])


def to_out(competition: Competition) -> CompetitionOut:
    return CompetitionOut(
        id=competition.id,
        title=competition.title,
        url=competition.url or "",
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
        crawl_status=competition.crawl_status or "",
        crawl_error=competition.crawl_error or "",
        source_title=competition.source_title or "",
        last_crawled=competition.last_crawled,
        created_at=competition.created_at,
        updated_at=competition.updated_at,
    )


@router.get("", response_model=CompetitionListResponse)
def list_competitions(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    tag: Optional[str] = None,
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
