from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.models import User, UserProfile


router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileResponse(BaseModel):
    university: str
    major: str
    grade: str
    interest_tags: List[str]
    bio: str


class ProfileUpdate(BaseModel):
    university: Optional[str] = None
    major: Optional[str] = None
    grade: Optional[str] = None
    interest_tags: Optional[List[str]] = None
    bio: Optional[str] = None


def _tags_to_string(tags: List[str]) -> str:
    return ",".join(t.strip() for t in tags if t and t.strip())


def _tags_from_string(value: str) -> List[str]:
    if not value:
        return []
    return [t.strip() for t in value.split(",") if t.strip()]


def _profile_to_response(profile: UserProfile) -> ProfileResponse:
    return ProfileResponse(
        university=profile.university or "",
        major=profile.major or "",
        grade=profile.grade or "",
        interest_tags=_tags_from_string(profile.interest_tags or ""),
        bio=profile.bio or "",
    )


@router.get("", response_model=ProfileResponse)
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        return ProfileResponse(
            university="",
            major="",
            grade="",
            interest_tags=[],
            bio="",
        )
    return _profile_to_response(profile)


@router.put("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    if payload.university is not None:
        profile.university = payload.university
    if payload.major is not None:
        profile.major = payload.major
    if payload.grade is not None:
        profile.grade = payload.grade
    if payload.interest_tags is not None:
        profile.interest_tags = _tags_to_string(payload.interest_tags)
    if payload.bio is not None:
        profile.bio = payload.bio

    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)
