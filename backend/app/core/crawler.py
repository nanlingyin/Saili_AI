"""Competition website crawler — ported from paqu/app.py."""
from __future__ import annotations

import datetime as dt
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.config import CRAWL_MAX_WORKERS, CRAWL_TIMEOUT_SECONDS
from app.core.models import Competition

logger = logging.getLogger(__name__)

STATUS_OPEN = "报名中"
STATUS_PENDING = "待确认"
STATUS_CLOSED = "可能已截止"
STATUS_FAILED = "抓取失败"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}

DATE_PATTERNS = [
    re.compile(r"(20\d{2})\s*年\s*(1[0-2]|0?[1-9])\s*月\s*(3[01]|[12]\d|0?[1-9])\s*日?"),
    re.compile(r"(20\d{2})[./-](1[0-2]|0?[1-9])[./-](3[01]|[12]\d|0?[1-9])"),
]

DEADLINE_HINTS = [
    "报名截止", "截止日期", "截止时间", "提交截止", "申请截止", "deadline", "due",
]

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

refresh_lock = threading.Lock()
refresh_state: dict[str, Any] = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "progress_done": 0,
    "progress_total": 0,
    "reason": None,
    "summary": {},
    "last_error": None,
}


def _normalize_space(text: str, max_len: int | None = None) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if max_len and len(cleaned) > max_len:
        return cleaned[:max_len].rstrip() + "..."
    return cleaned


def _parse_date(y: str, m: str, d: str) -> dt.date | None:
    try:
        return dt.date(int(y), int(m), int(d))
    except ValueError:
        return None


def _find_date_candidates(text: str) -> list[tuple[int, str, str]]:
    candidates: list[tuple[int, str, str]] = []
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            date_obj = _parse_date(*match.groups())
            if date_obj:
                candidates.append((match.start(), match.group(0), date_obj.isoformat()))
    return candidates


def _extract_deadline(text: str) -> tuple[str, str | None]:
    if not text:
        return "", None
    lowered = text.lower()
    candidates = _find_date_candidates(lowered)
    if not candidates:
        return "", None

    hint_positions = [lowered.find(h) for h in DEADLINE_HINTS if lowered.find(h) >= 0]
    today_iso = dt.date.today().isoformat()

    if hint_positions:
        best = min(
            candidates,
            key=lambda c: min(abs(c[0] - hp) for hp in hint_positions),
        )
        return best[1], best[2]

    future = [c for c in candidates if c[2] >= today_iso]
    if future:
        return min(future, key=lambda c: c[2])[1], min(future, key=lambda c: c[2])[2]

    latest = max(candidates, key=lambda c: c[2])
    return latest[1], latest[2]


def _decide_status(deadline_iso: str | None, crawl_error: str | None) -> str:
    if crawl_error:
        return STATUS_FAILED
    if not deadline_iso:
        return STATUS_PENDING
    if deadline_iso >= dt.date.today().isoformat():
        return STATUS_OPEN
    return STATUS_CLOSED


def _extract_intro(soup: BeautifulSoup, body_text: str) -> str:
    meta_tags = [
        soup.find("meta", attrs={"name": "description"}),
        soup.find("meta", attrs={"property": "og:description"}),
        soup.find("meta", attrs={"name": "keywords"}),
    ]
    for tag in meta_tags:
        if tag and tag.get("content"):
            return _normalize_space(tag.get("content", ""), max_len=220)

    for p in soup.find_all("p", limit=12):
        content = _normalize_space(p.get_text(" ", strip=True))
        if len(content) >= 30:
            return _normalize_space(content, max_len=220)

    return _normalize_space(body_text, max_len=220)


# ---------------------------------------------------------------------------
# crawl single competition
# ---------------------------------------------------------------------------

def _crawl_one(comp_id: int, comp_title: str, url: str) -> dict[str, Any]:
    timestamp = dt.datetime.now().isoformat(timespec="seconds")

    if not url:
        return {
            "id": comp_id,
            "description": "该赛事暂未提供可访问官网，请手动补充。",
            "deadline_text": "",
            "deadline_date": None,
            "crawl_status": STATUS_PENDING,
            "crawl_error": "无可用官网链接",
            "source_title": "",
            "last_crawled": timestamp,
        }

    try:
        response = requests.get(url, headers=HEADERS, timeout=CRAWL_TIMEOUT_SECONDS)
        response.raise_for_status()
        if response.encoding == "ISO-8859-1":
            response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")
        body_text = _normalize_space(soup.get_text(" ", strip=True), max_len=12000)
        intro = _extract_intro(soup, body_text)
        deadline_text, deadline_date = _extract_deadline(body_text)
        title = _normalize_space(
            soup.title.get_text(" ", strip=True) if soup.title else "",
            max_len=160,
        )

        return {
            "id": comp_id,
            "description": intro or f"{comp_title}官网抓取完成，但未提取到有效简介。",
            "deadline_text": deadline_text,
            "deadline_date": deadline_date,
            "crawl_status": _decide_status(deadline_date, None),
            "crawl_error": "",
            "source_title": title,
            "last_crawled": timestamp,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "id": comp_id,
            "description": "",
            "deadline_text": "",
            "deadline_date": None,
            "crawl_status": _decide_status(None, str(exc)),
            "crawl_error": _normalize_space(str(exc), max_len=180),
            "source_title": "",
            "last_crawled": timestamp,
        }


# ---------------------------------------------------------------------------
# persist results
# ---------------------------------------------------------------------------

def _persist_results(db: Session, results: list[dict[str, Any]]) -> None:
    for row in results:
        comp = db.query(Competition).filter(Competition.id == row["id"]).first()
        if not comp:
            continue
        comp.description = row["description"] or comp.description
        comp.crawl_status = row["crawl_status"]
        comp.crawl_error = row["crawl_error"]
        comp.source_title = row["source_title"]
        comp.last_crawled = dt.datetime.fromisoformat(row["last_crawled"]) if row["last_crawled"] else None

        if row["deadline_date"]:
            try:
                comp.signup_end = dt.datetime.fromisoformat(row["deadline_date"])
            except ValueError:
                pass
    db.commit()


def _summarize(db: Session) -> dict[str, int]:
    comps = db.query(Competition).filter(Competition.status == "published").all()
    summary: dict[str, int] = {
        "total": len(comps),
        STATUS_OPEN: 0,
        STATUS_PENDING: 0,
        STATUS_CLOSED: 0,
        STATUS_FAILED: 0,
    }
    for c in comps:
        key = c.crawl_status or STATUS_PENDING
        summary[key] = summary.get(key, 0) + 1
    return summary


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def get_refresh_state() -> dict[str, Any]:
    with refresh_lock:
        return dict(refresh_state)


def _set(**kwargs: Any) -> None:
    with refresh_lock:
        refresh_state.update(kwargs)


def _refresh_worker(db_factory, reason: str) -> None:
    """Background crawl worker. db_factory is a callable returning a new Session."""
    db = db_factory()
    try:
        comps = db.query(Competition).filter(Competition.status == "published").all()
        total = len(comps)
        _set(
            running=True,
            started_at=dt.datetime.now().isoformat(timespec="seconds"),
            finished_at=None,
            progress_done=0,
            progress_total=total,
            reason=reason,
            summary={},
            last_error=None,
        )

        items = [(c.id, c.title, c.url or "") for c in comps]
        results: list[dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=CRAWL_MAX_WORKERS) as pool:
            futures = {
                pool.submit(_crawl_one, cid, title, url): cid
                for cid, title, url in items
            }
            for future in as_completed(futures):
                cid = futures[future]
                try:
                    result = future.result()
                except Exception as exc:  # noqa: BLE001
                    result = {
                        "id": cid,
                        "description": "",
                        "deadline_text": "",
                        "deadline_date": None,
                        "crawl_status": STATUS_FAILED,
                        "crawl_error": _normalize_space(str(exc), max_len=180),
                        "source_title": "",
                        "last_crawled": dt.datetime.now().isoformat(timespec="seconds"),
                    }
                results.append(result)
                with refresh_lock:
                    refresh_state["progress_done"] += 1

        _persist_results(db, results)
        _set(summary=_summarize(db))
    except Exception as exc:  # noqa: BLE001
        logger.exception("refresh worker failed")
        _set(last_error=_normalize_space(str(exc), max_len=200))
    finally:
        _set(
            running=False,
            finished_at=dt.datetime.now().isoformat(timespec="seconds"),
        )
        db.close()


def trigger_refresh(db_factory, reason: str = "manual") -> bool:
    """Start a background crawl. Returns False if already running."""
    with refresh_lock:
        if refresh_state["running"]:
            return False
        refresh_state["running"] = True

    thread = threading.Thread(
        target=_refresh_worker, args=(db_factory, reason), daemon=True,
    )
    thread.start()
    return True
