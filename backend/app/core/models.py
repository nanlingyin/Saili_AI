from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.core.db import Base
from app.core.time import now_utc


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    role = Column(String(30), default="student", nullable=False)
    school = Column(String(255), default="", nullable=False)
    kicked_count = Column(Integer, default=0, nullable=False)
    missed_checkins = Column(Integer, default=0, nullable=False)
    completed_tasks = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    university = Column(String(255), default="")
    major = Column(String(255), default="")
    grade = Column(String(50), default="")
    interest_tags = Column(String(500), default="")
    bio = Column(Text, default="")
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True)
    source = Column(String(50), default="manual", nullable=False)
    level = Column(String(20), default="national", nullable=False)
    school = Column(String(255), default="ALL", nullable=False)
    creator_user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    organizer = Column(String(255))
    location = Column(String(255))
    signup_start = Column(DateTime)
    signup_end = Column(DateTime)
    event_start = Column(DateTime)
    event_end = Column(DateTime)
    reward = Column(String(255))
    requirements = Column(Text)
    contact_note = Column(String(255), default="")
    tags = Column(String(255))
    status = Column(String(20), default="pending", nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class CompetitionEnrollment(Base):
    __tablename__ = "competition_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "competition_id", name="uix_competition_enrollment"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))
    status = Column(String(20), default="registered", nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    submitted_at = Column(DateTime)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    school = Column(String(255), default="", nullable=False)
    leader_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    required_skills = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uix_team_member"),
    )

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skills = Column(String(255), nullable=False)
    status = Column(String(20), default="active", nullable=False)
    joined_at = Column(DateTime, default=now_utc, nullable=False)
    kicked_at = Column(DateTime)


class TeamTask(Base):
    __tablename__ = "team_tasks"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    assignee_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_at = Column(DateTime)
    status = Column(String(20), default="pending", nullable=False)
    overdue_flagged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    completed_at = Column(DateTime)


class UserAwardRecord(Base):
    __tablename__ = "user_award_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_name = Column(String(255), nullable=False)
    award_name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "competition_id", name="uix_fav"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "subscription_type", "target", name="uix_sub"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_type = Column(String(20), nullable=False)
    target = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)


class ReminderSetting(Base):
    __tablename__ = "reminder_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "days_before", name="uix_reminder_setting"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    days_before = Column(Integer, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)


class ReminderLog(Base):
    __tablename__ = "reminder_logs"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "competition_id",
            "days_before",
            name="uix_reminder_log",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    days_before = Column(Integer, nullable=False)
    sent_at = Column(DateTime, default=now_utc, nullable=False)


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, index=True)
    school = Column(String(255), nullable=False, index=True)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    pinned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class ForumReply(Base):
    __tablename__ = "forum_replies"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False, index=True)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class RecommendationRule(Base):
    __tablename__ = "recommendation_rules"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    weight = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=now_utc, nullable=False)


class IngestionSource(Base):
    __tablename__ = "ingestion_sources"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(100), unique=True, nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    config_json = Column(Text, nullable=False, default="{}")
    priority = Column(Integer, nullable=False, default=100)
    enabled = Column(Boolean, nullable=False, default=True)
    health_status = Column(String(20), nullable=False, default="healthy")
    failure_count = Column(Integer, nullable=False, default=0)
    failure_threshold = Column(Integer, nullable=False, default=3)
    last_sync_at = Column(DateTime)
    last_success_at = Column(DateTime)
    last_error = Column(Text)
    total_runs = Column(Integer, nullable=False, default=0)
    success_runs = Column(Integer, nullable=False, default=0)
    failure_runs = Column(Integer, nullable=False, default=0)
    parse_error_count = Column(Integer, nullable=False, default=0)
    freshness_hours = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class IngestionRawItem(Base):
    __tablename__ = "ingestion_raw_items"
    __table_args__ = (
        UniqueConstraint("source_id", "source_item_id", name="uix_ingest_raw_item"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(100), nullable=False, index=True)
    source_item_id = Column(String(255), nullable=False)
    source_url = Column(String(500))
    payload_json = Column(Text, nullable=False)
    payload_checksum = Column(String(64), nullable=False)
    extracted_json = Column(Text)
    extraction_status = Column(String(20), nullable=False, default="pending")
    parser_version = Column(String(20), nullable=False, default="v1")
    extractor_version = Column(String(50), nullable=False, default="rules-v1")
    fetched_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class CompetitionSourceLink(Base):
    __tablename__ = "competition_source_links"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "source_item_id",
            name="uix_competition_source_item",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    source_id = Column(String(100), nullable=False, index=True)
    source_item_id = Column(String(255), nullable=False)
    source_url = Column(String(500))
    parser_version = Column(String(20), nullable=False, default="v1")
    extractor_version = Column(String(50), nullable=False, default="rules-v1")
    fetched_at = Column(DateTime, default=now_utc, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)
