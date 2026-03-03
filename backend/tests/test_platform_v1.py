def _login(client, username: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _register_and_login(client, username: str, email: str, password: str) -> str:
    register = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert register.status_code == 200
    return _login(client, username, password)


def _admin_headers(client) -> dict:
    token = _login(client, "admin", "admin123")
    return {"Authorization": f"Bearer {token}"}


def _user_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_and_publish_competition(client, headers: dict, payload: dict) -> int:
    create = client.post("/api/v1/admin/competitions", json=payload, headers=headers)
    assert create.status_code == 200
    cid = create.json()["id"]
    publish = client.post(f"/api/v1/admin/competitions/{cid}/publish", headers=headers)
    assert publish.status_code == 200
    return cid


def test_team_requires_skill_tags(client):
    token = _register_and_login(client, "team_leader", "leader@example.com", "pass1234")
    headers = _user_headers(token)

    empty_resp = client.post(
        "/api/v1/teams",
        json={"name": "A队", "required_skills": []},
        headers=headers,
    )
    assert empty_resp.status_code == 400

    invalid_resp = client.post(
        "/api/v1/teams",
        json={"name": "A队", "required_skills": ["会摸鱼"]},
        headers=headers,
    )
    assert invalid_resp.status_code == 400

    ok_resp = client.post(
        "/api/v1/teams",
        json={"name": "A队", "required_skills": ["会编程", "会PPT"]},
        headers=headers,
    )
    assert ok_resp.status_code == 200
    body = ok_resp.json()
    assert body["required_skills"] == ["会编程", "会PPT"]


def test_competition_smart_filters(client):
    admin_headers = _admin_headers(client)

    _create_and_publish_competition(
        client,
        admin_headers,
        {
            "title": "挑战杯创新项目",
            "description": "国家级赛事",
            "tags": ["挑战杯", "创新"],
        },
    )
    _create_and_publish_competition(
        client,
        admin_headers,
        {
            "title": "不知名水赛凑学分活动",
            "description": "水赛",
            "tags": ["水赛"],
        },
    )

    high_value = client.get("/api/v1/competitions?goal=保研加分")
    assert high_value.status_code == 200
    titles = [item["title"] for item in high_value.json()["items"]]
    assert "挑战杯创新项目" in titles
    assert "不知名水赛凑学分活动" not in titles

    no_low_value = client.get("/api/v1/competitions?hide_low_value=true")
    assert no_low_value.status_code == 200
    titles2 = [item["title"] for item in no_low_value.json()["items"]]
    assert "挑战杯创新项目" in titles2
    assert "不知名水赛凑学分活动" not in titles2


def test_school_current_and_admin_csv_export(client):
    admin_headers = _admin_headers(client)
    user_token = _register_and_login(client, "stu_a", "stu_a@example.com", "pass1234")
    user_headers = _user_headers(user_token)

    cid = _create_and_publish_competition(
        client,
        admin_headers,
        {
            "title": "校级选拔赛",
            "school": "XX大学",
            "description": "仅本校",
            "tags": ["挑战杯"],
        },
    )

    school_view = client.get("/api/v1/competitions/school/current?school=XX大学")
    assert school_view.status_code == 200
    assert any(item["id"] == cid for item in school_view.json())

    enroll = client.post(f"/api/v1/competitions/{cid}/enroll", headers=user_headers)
    assert enroll.status_code == 200
    submit = client.post(f"/api/v1/competitions/{cid}/submit", headers=user_headers)
    assert submit.status_code == 200

    csv_resp = client.get(f"/api/v1/admin/competitions/{cid}/registrations/export.csv", headers=admin_headers)
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"].startswith("text/csv")
    assert "stu_a" in csv_resp.text
    assert "submitted" in csv_resp.text


def test_resume_pdf_export(client):
    token = _register_and_login(client, "resume_user", "resume@example.com", "pass1234")
    headers = _user_headers(token)

    add_record = client.post(
        "/api/v1/resume/records",
        json={"competition_name": "挑战杯", "award_name": "省一等奖", "year": 2025},
        headers=headers,
    )
    assert add_record.status_code == 200

    pdf_resp = client.get("/api/v1/resume/pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"].startswith("application/pdf")
    assert len(pdf_resp.content) > 100
