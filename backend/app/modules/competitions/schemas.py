from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CompetitionBase(BaseModel):
    title: str
    url: Optional[str] = ""
    description: Optional[str] = None
    organizer: Optional[str] = None
    location: Optional[str] = None
    signup_start: Optional[datetime] = None
    signup_end: Optional[datetime] = None
    event_start: Optional[datetime] = None
    event_end: Optional[datetime] = None
    reward: Optional[str] = None
    requirements: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class CompetitionCreate(CompetitionBase):
    pass


class CompetitionUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    organizer: Optional[str] = None
    location: Optional[str] = None
    signup_start: Optional[datetime] = None
    signup_end: Optional[datetime] = None
    event_start: Optional[datetime] = None
    event_end: Optional[datetime] = None
    reward: Optional[str] = None
    requirements: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class CompetitionOut(CompetitionBase):
    id: int
    status: str
    source: str
    crawl_status: Optional[str] = ""
    crawl_error: Optional[str] = ""
    source_title: Optional[str] = ""
    last_crawled: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CompetitionListResponse(BaseModel):
    items: List[CompetitionOut]
    total: int
    page: int
    page_size: int


def tags_to_string(tags: List[str]) -> str:
    cleaned = [tag.strip() for tag in tags if tag and tag.strip()]
    return ",".join(cleaned)


def tags_from_string(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]
