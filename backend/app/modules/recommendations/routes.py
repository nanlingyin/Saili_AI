from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.models import Competition, RecommendationRule, Subscription, User, UserProfile
from app.core.time import now_utc
from app.modules.competitions.schemas import CompetitionOut, tags_from_string

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

DEFAULT_RULES = {
    "tag_match": 10,
    "deadline_soon": 3,
    "new_competition": 2,
    "major_match": 5,
    "interest_match": 8,
}


def ensure_rules(db: Session) -> dict:
    rules = {rule.key: rule.weight for rule in db.query(RecommendationRule).all()}
    if rules:
        return rules

    for key, weight in DEFAULT_RULES.items():
        db.add(RecommendationRule(key=key, weight=weight))
    db.commit()
    return DEFAULT_RULES


def score_competition(
    competition: Competition,
    rules: dict,
    subscribed_tags: set[str],
    user_major: str = "",
    user_interest_tags: set[str] | None = None,
) -> int:
    score = 0
    tags = set(tags_from_string(competition.tags))
    if subscribed_tags and tags.intersection(subscribed_tags):
        score += rules.get("tag_match", 0)

    if competition.signup_end:
        if competition.signup_end <= now_utc() + timedelta(days=7):
            score += rules.get("deadline_soon", 0)

    if competition.created_at >= now_utc() - timedelta(days=7):
        score += rules.get("new_competition", 0)

    # 专业匹配：竞赛标签或描述中包含用户专业关键词
    if user_major:
        major_lower = user_major.lower()
        title_desc = (competition.title or "").lower() + (competition.description or "").lower()
        tags_lower = {t.lower() for t in tags}
        if major_lower in title_desc or major_lower in tags_lower:
            score += rules.get("major_match", 0)

    # 兴趣标签匹配：用户兴趣标签与竞赛标签取交集
    if user_interest_tags and tags:
        comp_tags_lower = {t.lower() for t in tags}
        interest_lower = {t.lower() for t in user_interest_tags}
        if comp_tags_lower.intersection(interest_lower):
            score += rules.get("interest_match", 0)

    return score


@router.get("", response_model=list[CompetitionOut])
def list_recommendations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
) -> list[CompetitionOut]:
    if limit < 1:
        limit = 10
    rules = ensure_rules(db)
    subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.subscription_type == "tag",
        )
        .all()
    )
    subscribed_tags = {item.target for item in subscriptions}

    # 查询用户画像用于个性化推荐
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    user_major = profile.major if profile and profile.major else ""
    user_interest_tags: set[str] = set()
    if profile and profile.interest_tags:
        user_interest_tags = {t.strip() for t in profile.interest_tags.split(",") if t.strip()}

    competitions = (
        db.query(Competition)
        .filter(Competition.status == "published")
        .all()
    )

    scored = [
        (
            score_competition(item, rules, subscribed_tags, user_major, user_interest_tags),
            item,
        )
        for item in competitions
    ]
    scored.sort(key=lambda entry: entry[0], reverse=True)

    items = [item for score, item in scored if score > 0][:limit]
    return [
        CompetitionOut(
            id=item.id,
            title=item.title,
            level=item.level,
            school=item.school,
            description=item.description,
            organizer=item.organizer,
            location=item.location,
            signup_start=item.signup_start,
            signup_end=item.signup_end,
            event_start=item.event_start,
            event_end=item.event_end,
            reward=item.reward,
            requirements=item.requirements,
            contact_note=item.contact_note,
            tags=tags_from_string(item.tags),
            status=item.status,
            source=item.source,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]
