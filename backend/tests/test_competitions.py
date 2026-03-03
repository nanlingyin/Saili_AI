def test_competition_list_after_publish(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/admin/competitions",
        json={
            "title": "测试竞赛",
            "description": "描述",
            "tags": ["英语"],
        },
        headers=headers,
    )
    assert create.status_code == 200
    competition_id = create.json()["id"]

    publish = client.post(
        f"/api/v1/admin/competitions/{competition_id}/publish",
        headers=headers,
    )
    assert publish.status_code == 200

    listing = client.get("/api/v1/competitions")
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert len(items) == 1


def test_competition_level_filter(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    school = client.post(
        "/api/v1/admin/competitions",
        json={
            "title": "校赛A",
            "level": "school",
        },
        headers=headers,
    )
    assert school.status_code == 200

    national = client.post(
        "/api/v1/admin/competitions",
        json={
            "title": "国赛B",
            "level": "national",
        },
        headers=headers,
    )
    assert national.status_code == 200

    school_id = school.json()["id"]
    national_id = national.json()["id"]

    assert client.post(f"/api/v1/admin/competitions/{school_id}/publish", headers=headers).status_code == 200
    assert client.post(f"/api/v1/admin/competitions/{national_id}/publish", headers=headers).status_code == 200

    national_listing = client.get("/api/v1/competitions?level=national")
    assert national_listing.status_code == 200
    titles = [item["title"] for item in national_listing.json()["items"]]
    assert "国赛B" in titles
    assert "校赛A" not in titles
