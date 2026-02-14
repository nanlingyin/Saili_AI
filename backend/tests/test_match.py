def _admin_headers(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_match_endpoint_returns_ranked_items(client):
    headers = _admin_headers(client)
    create = client.post(
        "/api/v1/admin/competitions",
        headers=headers,
        json={
            "title": "AI 编程挑战赛",
            "description": "面向计算机与人工智能方向的程序设计竞赛",
            "tags": ["编程", "AI"],
        },
    )
    assert create.status_code == 200
    comp_id = create.json()["id"]
    publish = client.post(f"/api/v1/admin/competitions/{comp_id}/publish", headers=headers)
    assert publish.status_code == 200

    response = client.post("/api/v1/match", json={"major": "计算机科学与技术", "top_k": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["major"] == "计算机科学与技术"
    assert isinstance(body["matches"], list)
    assert len(body["matches"]) >= 1
    assert len(body["matches"]) <= 5
    first = body["matches"][0]
    assert first["id"] == comp_id
    assert "score" in first
    assert "reason" in first


def test_match_endpoint_validates_major(client):
    response = client.post("/api/v1/match", json={"major": "   ", "top_k": 8})
    assert response.status_code == 400
