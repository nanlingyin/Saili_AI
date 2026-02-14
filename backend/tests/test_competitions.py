
def test_competition_list_after_publish(client):
    website = "https://example.com/contest"
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
            "url": website,
            "description": "描述",
            "tags": ["英语"],
        },
        headers=headers,
    )
    assert create.status_code == 200
    assert create.json()["url"] == website
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
    assert items[0]["url"] == website
