from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.matcher import match_by_major

router = APIRouter(prefix="/match", tags=["match"])


class MatchRequest(BaseModel):
    major: str
    top_k: int = 8


@router.post("")
def smart_match(
    payload: MatchRequest,
    db: Session = Depends(get_db),
) -> dict:
    major = payload.major.strip()
    if not major:
        raise HTTPException(status_code=400, detail="请输入专业名称")
    top_k = max(1, min(payload.top_k, 20))
    matches = match_by_major(db, major, top_k=top_k)
    return {"major": major, "matches": matches}
