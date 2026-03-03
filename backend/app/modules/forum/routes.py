from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_user_role, is_platform_admin
from app.core.db import get_db
from app.core.models import ForumPost, ForumReply, User
from app.core.time import now_utc

router = APIRouter(prefix="/forum", tags=["forum"])


class ForumPostCreate(BaseModel):
    title: str
    content: str
    school: Optional[str] = None


class ForumReplyCreate(BaseModel):
    content: str


class ForumReplyOut(BaseModel):
    id: int
    post_id: int
    author_user_id: int
    author_username: str
    content: str
    created_at: str


class ForumPostOut(BaseModel):
    id: int
    school: str
    author_user_id: int
    author_username: str
    title: str
    content: str
    pinned: bool
    created_at: str
    updated_at: str
    replies: list[ForumReplyOut] = []


class ForumPostListResponse(BaseModel):
    items: list[ForumPostOut]
    total: int
    page: int
    page_size: int


def _can_moderate(user: User, school: str) -> bool:
    if is_platform_admin(user):
        return True
    return user.school == school and get_user_role(user) in {"school_admin", "student_admin"}


def _to_reply_out(reply: ForumReply, user_map: dict[int, User]) -> ForumReplyOut:
    author = user_map.get(reply.author_user_id)
    return ForumReplyOut(
        id=reply.id,
        post_id=reply.post_id,
        author_user_id=reply.author_user_id,
        author_username=author.username if author else f"user-{reply.author_user_id}",
        content=reply.content,
        created_at=reply.created_at.isoformat(),
    )


def _to_post_out(
    post: ForumPost,
    user_map: dict[int, User],
    replies: list[ForumReply] | None = None,
) -> ForumPostOut:
    author = user_map.get(post.author_user_id)
    reply_items = replies or []
    return ForumPostOut(
        id=post.id,
        school=post.school,
        author_user_id=post.author_user_id,
        author_username=author.username if author else f"user-{post.author_user_id}",
        title=post.title,
        content=post.content,
        pinned=post.pinned,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
        replies=[_to_reply_out(item, user_map) for item in reply_items],
    )


@router.get("/posts", response_model=ForumPostListResponse)
def list_forum_posts(
    school: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumPostListResponse:
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    query = db.query(ForumPost)

    if is_platform_admin(current_user):
        if school:
            query = query.filter(ForumPost.school == school.strip())
    else:
        if not current_user.school:
            raise HTTPException(status_code=400, detail="school not assigned")
        query = query.filter(ForumPost.school == current_user.school)

    if q:
        like = f"%{q.strip()}%"
        query = query.filter((ForumPost.title.ilike(like)) | (ForumPost.content.ilike(like)))

    total = query.count()
    posts = (
        query.order_by(ForumPost.pinned.desc(), ForumPost.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    author_ids = {item.author_user_id for item in posts}
    users = db.query(User).filter(User.id.in_(author_ids)).all() if author_ids else []
    user_map = {item.id: item for item in users}

    return ForumPostListResponse(
        items=[_to_post_out(item, user_map) for item in posts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/posts/{post_id}", response_model=ForumPostOut)
def get_forum_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumPostOut:
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    if not is_platform_admin(current_user) and current_user.school != post.school:
        raise HTTPException(status_code=403, detail="cross-school access denied")

    replies = (
        db.query(ForumReply)
        .filter(ForumReply.post_id == post_id)
        .order_by(ForumReply.created_at.asc())
        .all()
    )
    author_ids = {post.author_user_id, *(item.author_user_id for item in replies)}
    users = db.query(User).filter(User.id.in_(author_ids)).all()
    user_map = {item.id: item for item in users}

    return _to_post_out(post, user_map, replies=replies)


@router.post("/posts", response_model=ForumPostOut)
def create_forum_post(
    payload: ForumPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumPostOut:
    title = payload.title.strip()
    content = payload.content.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    if is_platform_admin(current_user):
        school = (payload.school or "").strip()
        if not school:
            raise HTTPException(status_code=400, detail="school is required")
    else:
        school = (current_user.school or "").strip()
        if not school:
            raise HTTPException(status_code=400, detail="school not assigned")

    post = ForumPost(
        school=school,
        author_user_id=current_user.id,
        title=title,
        content=content,
        pinned=False,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return _to_post_out(post, {current_user.id: current_user})


@router.post("/posts/{post_id}/replies", response_model=ForumReplyOut)
def create_forum_reply(
    post_id: int,
    payload: ForumReplyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumReplyOut:
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    if not is_platform_admin(current_user) and current_user.school != post.school:
        raise HTTPException(status_code=403, detail="cross-school access denied")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    reply = ForumReply(
        post_id=post_id,
        author_user_id=current_user.id,
        content=content,
    )
    post.updated_at = now_utc()
    db.add(reply)
    db.commit()
    db.refresh(reply)

    return _to_reply_out(reply, {current_user.id: current_user})


@router.post("/posts/{post_id}/pin")
def pin_forum_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    if not _can_moderate(current_user, post.school):
        raise HTTPException(status_code=403, detail="moderator only")

    post.pinned = not post.pinned
    post.updated_at = now_utc()
    db.commit()
    return {"status": "ok", "pinned": post.pinned}


@router.delete("/posts/{post_id}")
def delete_forum_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    if not _can_moderate(current_user, post.school):
        raise HTTPException(status_code=403, detail="moderator only")

    db.query(ForumReply).filter(ForumReply.post_id == post_id).delete()
    db.delete(post)
    db.commit()
    return {"status": "ok"}


@router.delete("/replies/{reply_id}")
def delete_forum_reply(
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    reply = db.query(ForumReply).filter(ForumReply.id == reply_id).first()
    if not reply:
        raise HTTPException(status_code=404, detail="reply not found")

    post = db.query(ForumPost).filter(ForumPost.id == reply.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    if not _can_moderate(current_user, post.school):
        raise HTTPException(status_code=403, detail="moderator only")

    db.delete(reply)
    post.updated_at = now_utc()
    db.commit()
    return {"status": "ok"}
