import json
import os
from pathlib import Path


def _admin_headers(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _write_json(path: str, payload) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_ingestion_extraction_and_review_flags(client):
    source_path = os.environ["STABLE_SOURCE_PATH"]
    _write_json(
        source_path,
        [
            {
                "source_item_id": "stable-1",
                "title": "英语演讲比赛",
                "description": "面向全校学生，报名截止 2026-03-10",
                "signup_end": "2026-03-10T00:00:00",
                "tags": ["英语"],
            },
            {
                "source_item_id": "stable-2",
                "description": "缺少标题，需人工审核",
                "signup_end": "2026-03-11T00:00:00",
            },
        ],
    )

    headers = _admin_headers(client)
    resp = client.post("/api/v1/admin/ingest/source", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["created"] == 1
    assert body["parse_errors"] == 1

    competitions = client.get("/api/v1/admin/competitions", headers=headers)
    assert competitions.status_code == 200
    items = competitions.json()
    assert len(items) == 1
    assert items[0]["title"] == "英语演讲比赛"


def test_ingestion_idempotent_and_cross_source_dedup(client):
    source_path = os.environ["STABLE_SOURCE_PATH"]
    fallback_path = os.environ["FALLBACK_SOURCE_PATH"]
    _write_json(
        source_path,
        [
            {
                "source_item_id": "stable-100",
                "title": "AI 创新赛",
                "description": "第一来源",
                "signup_end": "2026-04-01T00:00:00",
            }
        ],
    )

    headers = _admin_headers(client)
    first = client.post("/api/v1/admin/ingest/source", headers=headers)
    assert first.status_code == 200
    assert first.json()["created"] == 1

    second = client.post("/api/v1/admin/ingest/source", headers=headers)
    assert second.status_code == 200
    assert second.json()["created"] == 0
    assert second.json()["updated"] == 0
    assert second.json()["skipped"] >= 1

    _write_json(
        fallback_path,
        [
            {
                "source_item_id": "fallback-200",
                "title": "AI 创新赛",
                "description": "兜底来源",
                "signup_end": "2026-04-01T00:00:00",
            }
        ],
    )
    from_fallback = client.post(
        "/api/v1/admin/ingest/source",
        json={"source_id": "fallback_file"},
        headers=headers,
    )
    assert from_fallback.status_code == 200
    assert from_fallback.json()["created"] == 0
    assert from_fallback.json()["updated"] == 1

    competitions = client.get("/api/v1/admin/competitions", headers=headers)
    assert competitions.status_code == 200
    assert len(competitions.json()) == 1


def test_ingestion_auto_fallback_when_primary_fails(client):
    source_path = Path(os.environ["STABLE_SOURCE_PATH"])
    fallback_path = os.environ["FALLBACK_SOURCE_PATH"]
    _write_json(
        fallback_path,
        [
            {
                "source_item_id": "fallback-1",
                "title": "数学建模竞赛",
                "description": "来自兜底源",
                "signup_end": "2026-05-01T00:00:00",
            }
        ],
    )
    if source_path.exists():
        source_path.unlink()

    headers = _admin_headers(client)
    resp = client.post("/api/v1/admin/ingest/source", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["fallback_used"] is True
    assert body["degraded_from"] == "stable_primary"
    assert body["source"] == "fallback_file"

    sources = client.get("/api/v1/admin/ingest/sources", headers=headers)
    assert sources.status_code == 200
    source_items = sources.json()["items"]
    primary = next(item for item in source_items if item["source_id"] == "stable_primary")
    assert primary["health_status"] in {"warning", "degraded"}
