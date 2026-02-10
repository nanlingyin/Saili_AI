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
    created_at = Column(DateTime, default=now_utc, nullable=False)


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True)
    source = Column(String(50), default="manual", nullable=False)
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
    tags = Column(String(255))
    status = Column(String(20), default="pending", nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)


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
