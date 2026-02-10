from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.models import Competition, Favorite, Subscription, User
from app.modules.competitions.schemas import CompetitionOut, tags_from_string

router = APIRouter(prefix="", tags=["favorites"])


class SubscriptionCreate(BaseModel):
    subscription_type: str
    target: str


@router.get("/favorites", response_model=list[CompetitionOut])
def list_favorites(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CompetitionOut]:
    favorites = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id)
        .all()
    )
    competition_ids = [fav.competition_id for fav in favorites]
    if not competition_ids:
        return []

    competitions = (
        db.query(Competition)
        .filter(Competition.id.in_(competition_ids))
        .all()
    )

    return [
        CompetitionOut(
            id=item.id,
            title=item.title,
            description=item.description,
            organizer=item.organizer,
            location=item.location,
            signup_start=item.signup_start,
            signup_end=item.signup_end,
            event_start=item.event_start,
            event_end=item.event_end,
            reward=item.reward,
            requirements=item.requirements,
            tags=tags_from_string(item.tags),
            status=item.status,
            source=item.source,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in competitions
    ]


@router.post("/favorites/{competition_id}")
def add_favorite(
    competition_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    competition = (
        db.query(Competition)
        .filter(Competition.id == competition_id, Competition.status == "published")
        .first()
    )
    if not competition:
        raise HTTPException(status_code=404, detail="competition not found")

    existing = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user.id,
            Favorite.competition_id == competition_id,
        )
        .first()
    )
    if existing:
        return {"status": "ok"}

    favorite = Favorite(user_id=user.id, competition_id=competition_id)
    db.add(favorite)
    db.commit()
    return {"status": "ok"}


@router.delete("/favorites/{competition_id}")
def remove_favorite(
    competition_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user.id,
            Favorite.competition_id == competition_id,
        )
        .first()
    )
    if favorite:
        db.delete(favorite)
        db.commit()
    return {"status": "ok"}


@router.get("/subscriptions", response_model=list[SubscriptionCreate])
def list_subscriptions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SubscriptionCreate]:
    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id)
        .all()
    )
    return [
        SubscriptionCreate(
            subscription_type=item.subscription_type,
            target=item.target,
        )
        for item in subscriptions
    ]


@router.post("/subscriptions")
def add_subscription(
    payload: SubscriptionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if payload.subscription_type not in {"tag", "competition"}:
        raise HTTPException(status_code=400, detail="invalid subscription type")

    if payload.subscription_type == "competition":
        if not payload.target.isdigit():
            raise HTTPException(status_code=400, detail="invalid competition target")
        if not db.query(Competition).filter(Competition.id == int(payload.target)).first():
            raise HTTPException(status_code=404, detail="competition not found")

    existing = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.subscription_type == payload.subscription_type,
            Subscription.target == payload.target,
        )
        .first()
    )
    if existing:
        return {"status": "ok"}

    subscription = Subscription(
        user_id=user.id,
        subscription_type=payload.subscription_type,
        target=payload.target,
    )
    db.add(subscription)
    db.commit()
    return {"status": "ok"}


@router.delete("/subscriptions")
def remove_subscription(
    subscription_type: str,
    target: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.subscription_type == subscription_type,
            Subscription.target == target,
        )
        .first()
    )
    if subscription:
        db.delete(subscription)
        db.commit()
    return {"status": "ok"}
