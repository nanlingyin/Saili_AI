from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.models import ReminderSetting, User

router = APIRouter(prefix="/reminders", tags=["reminders"])


class ReminderSettingIn(BaseModel):
    days_before: int
    enabled: bool = True


@router.get("/settings", response_model=list[ReminderSettingIn])
def list_settings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReminderSettingIn]:
    settings = (
        db.query(ReminderSetting)
        .filter(ReminderSetting.user_id == user.id)
        .all()
    )
    return [
        ReminderSettingIn(days_before=item.days_before, enabled=item.enabled)
        for item in settings
    ]


@router.post("/settings")
def upsert_setting(
    payload: ReminderSettingIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if payload.days_before < 0:
        raise HTTPException(status_code=400, detail="invalid days_before")

    setting = (
        db.query(ReminderSetting)
        .filter(
            ReminderSetting.user_id == user.id,
            ReminderSetting.days_before == payload.days_before,
        )
        .first()
    )
    if setting:
        setting.enabled = payload.enabled
    else:
        setting = ReminderSetting(
            user_id=user.id,
            days_before=payload.days_before,
            enabled=payload.enabled,
        )
        db.add(setting)

    db.commit()
    return {"status": "ok"}