from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.models import Team, TeamMember, TeamTask, User
from app.core.time import now_utc

router = APIRouter(prefix="/teams", tags=["teams"])

SKILL_TAGS = ["会PPT", "会编程", "会设计", "会写文案", "曾获奖"]


def tags_to_string(tags: list[str]) -> str:
    return ",".join([item.strip() for item in tags if item and item.strip()])


def tags_from_string(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_skill_tags(tags: list[str]) -> list[str]:
    cleaned = [item.strip() for item in tags if item and item.strip()]
    if not cleaned:
        raise HTTPException(status_code=400, detail="at least one skill tag is required")
    invalid = [item for item in cleaned if item not in SKILL_TAGS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"invalid skill tags: {','.join(invalid)}")
    return cleaned


class TeamCreate(BaseModel):
    name: str
    school: str = ""
    required_skills: list[str] = Field(default_factory=list)


class TeamOut(BaseModel):
    id: int
    name: str
    school: str
    leader_user_id: int
    required_skills: list[str]


class TeamMemberAdd(BaseModel):
    user_id: int
    skills: list[str] = Field(default_factory=list)


class TeamTaskCreate(BaseModel):
    assignee_user_id: int
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None


class TeamTaskCheckIn(BaseModel):
    note: Optional[str] = None


class TeamCreditOut(BaseModel):
    user_id: int
    kicked_count: int
    completion_rate: float
    missed_checkins: int


def _get_team_or_404(db: Session, team_id: int) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="team not found")
    return team


def _require_team_leader(team: Team, user: User) -> None:
    if team.leader_user_id != user.id:
        raise HTTPException(status_code=403, detail="only leader can perform this action")


@router.get("/skill-tags", response_model=list[str])
def get_skill_tags() -> list[str]:
    return SKILL_TAGS


@router.post("", response_model=TeamOut)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamOut:
    skills = validate_skill_tags(payload.required_skills)
    team = Team(
        name=payload.name.strip(),
        school=payload.school.strip(),
        leader_user_id=current_user.id,
        required_skills=tags_to_string(skills),
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    leader_member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        skills=tags_to_string(skills),
        status="active",
    )
    db.add(leader_member)
    db.commit()

    return TeamOut(
        id=team.id,
        name=team.name,
        school=team.school,
        leader_user_id=team.leader_user_id,
        required_skills=tags_from_string(team.required_skills),
    )


@router.post("/{team_id}/members")
def add_team_member(
    team_id: int,
    payload: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    team = _get_team_or_404(db, team_id)
    _require_team_leader(team, current_user)

    member_user = db.query(User).filter(User.id == payload.user_id).first()
    if not member_user:
        raise HTTPException(status_code=404, detail="user not found")

    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == payload.user_id)
        .first()
    )
    if existing and existing.status == "active":
        raise HTTPException(status_code=400, detail="user already in team")

    skills = validate_skill_tags(payload.skills)
    if existing:
        existing.skills = tags_to_string(skills)
        existing.status = "active"
        existing.joined_at = now_utc()
        existing.kicked_at = None
    else:
        db.add(
            TeamMember(
                team_id=team_id,
                user_id=payload.user_id,
                skills=tags_to_string(skills),
                status="active",
            )
        )

    db.commit()
    return {"status": "ok"}


@router.post("/{team_id}/members/{user_id}/kick")
def kick_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    team = _get_team_or_404(db, team_id)
    _require_team_leader(team, current_user)

    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
            TeamMember.status == "active",
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="active member not found")

    member.status = "kicked"
    member.kicked_at = now_utc()

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.kicked_count = (user.kicked_count or 0) + 1

    db.commit()
    return {"status": "ok"}


@router.get("/{team_id}/members/{user_id}/credit", response_model=TeamCreditOut)
def get_member_credit(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamCreditOut:
    team = _get_team_or_404(db, team_id)
    _require_team_leader(team, current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    total_assigned = (
        db.query(TeamTask)
        .filter(TeamTask.team_id == team_id, TeamTask.assignee_user_id == user_id)
        .count()
    )
    completed = (
        db.query(TeamTask)
        .filter(
            TeamTask.team_id == team_id,
            TeamTask.assignee_user_id == user_id,
            TeamTask.status == "completed",
        )
        .count()
    )
    completion_rate = 0.0 if total_assigned == 0 else completed / total_assigned

    return TeamCreditOut(
        user_id=user.id,
        kicked_count=user.kicked_count or 0,
        completion_rate=round(completion_rate, 4),
        missed_checkins=user.missed_checkins or 0,
    )


@router.post("/{team_id}/tasks")
def create_team_task(
    team_id: int,
    payload: TeamTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    team = _get_team_or_404(db, team_id)
    _require_team_leader(team, current_user)

    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == payload.assignee_user_id,
            TeamMember.status == "active",
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=400, detail="assignee must be an active member")

    task = TeamTask(
        team_id=team_id,
        assignee_user_id=payload.assignee_user_id,
        title=payload.title,
        description=payload.description,
        due_at=payload.due_at,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "status": task.status}


@router.post("/tasks/{task_id}/checkin")
def checkin_task(
    task_id: int,
    payload: TeamTaskCheckIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    task = db.query(TeamTask).filter(TeamTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    if task.assignee_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="only assignee can check in")

    if task.status != "completed":
        task.status = "completed"
        task.completed_at = now_utc()
        current_user.completed_tasks = (current_user.completed_tasks or 0) + 1
        db.commit()

    return {"status": "ok"}


@router.post("/{team_id}/tasks/audit-overdue")
def audit_overdue_tasks(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    team = _get_team_or_404(db, team_id)
    _require_team_leader(team, current_user)

    overdue_tasks = (
        db.query(TeamTask)
        .filter(
            TeamTask.team_id == team_id,
            TeamTask.status == "pending",
            TeamTask.due_at.isnot(None),
            TeamTask.due_at < now_utc(),
            TeamTask.overdue_flagged.is_(False),
        )
        .all()
    )

    affected = 0
    for task in overdue_tasks:
        assignee = db.query(User).filter(User.id == task.assignee_user_id).first()
        if assignee:
            assignee.missed_checkins = (assignee.missed_checkins or 0) + 1
            affected += 1
        task.overdue_flagged = True

    db.commit()
    return {"overdue_flagged": len(overdue_tasks), "users_updated": affected}
