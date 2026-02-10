from typing import Optional

from sqlalchemy.orm import Session

from app.core.email import send_email
from app.core.models import Competition, Favorite, ReminderLog, ReminderSetting, Subscription, User
from app.core.time import now_utc


def parse_tags(value: Optional[str]) -> set[str]:
    if not value:
        return set()
    return {tag.strip() for tag in value.split(",") if tag.strip()}


def send_due_reminders(db: Session) -> int:
    users = db.query(User).all()
    settings = db.query(ReminderSetting).filter(ReminderSetting.enabled.is_(True)).all()
    favorites = db.query(Favorite).all()
    subscriptions = db.query(Subscription).all()
    competitions = db.query(Competition).filter(Competition.status == "published").all()

    settings_by_user = {}
    for setting in settings:
        settings_by_user.setdefault(setting.user_id, []).append(setting.days_before)

    favorites_by_user = {}
    for favorite in favorites:
        favorites_by_user.setdefault(favorite.user_id, set()).add(favorite.competition_id)

    subscriptions_by_user = {}
    for subscription in subscriptions:
        subscriptions_by_user.setdefault(subscription.user_id, []).append(subscription)

    now = now_utc()
    sent = 0

    for user in users:
        user_settings = settings_by_user.get(user.id, [])
        if not user_settings:
            continue

        user_favorites = favorites_by_user.get(user.id, set())
        user_subscriptions = subscriptions_by_user.get(user.id, [])
        subscribed_tags = {
            sub.target for sub in user_subscriptions if sub.subscription_type == "tag"
        }
        subscribed_competitions = {
            int(sub.target)
            for sub in user_subscriptions
            if sub.subscription_type == "competition" and sub.target.isdigit()
        }

        for competition in competitions:
            if not competition.signup_end:
                continue

            days_before = (competition.signup_end.date() - now.date()).days
            if days_before not in user_settings:
                continue

            tags = parse_tags(competition.tags)
            relevant = (
                competition.id in user_favorites
                or competition.id in subscribed_competitions
                or (subscribed_tags and tags.intersection(subscribed_tags))
            )
            if not relevant:
                continue

            existing = (
                db.query(ReminderLog)
                .filter(
                    ReminderLog.user_id == user.id,
                    ReminderLog.competition_id == competition.id,
                    ReminderLog.days_before == days_before,
                )
                .first()
            )
            if existing:
                continue

            subject = f"竞赛截止提醒：{competition.title}"
            body = (
                f"{competition.title} 将在 {competition.signup_end} 截止。\n"
                "请及时查看报名信息。"
            )
            send_email(user.email, subject, body)
            db.add(
                ReminderLog(
                    user_id=user.id,
                    competition_id=competition.id,
                    days_before=days_before,
                )
            )
            sent += 1

    db.commit()
    return sent
