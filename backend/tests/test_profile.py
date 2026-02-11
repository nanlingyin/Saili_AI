"""Tests for the profile module (GET / PUT /api/v1/profile)."""


def _register_and_login(client, username="testuser", email="test@example.com", password="pass123"):
    client.post("/api/v1/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": password,
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- 7.1 成功场景 ---

def test_get_profile_empty(client):
    """未填写过资料时返回全空默认对象"""
    headers = _register_and_login(client)
    resp = client.get("/api/v1/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["university"] == ""
    assert data["major"] == ""
    assert data["grade"] == ""
    assert data["interest_tags"] == []
    assert data["bio"] == ""


def test_put_profile_create(client):
    """首次 PUT 创建资料"""
    headers = _register_and_login(client)
    payload = {
        "university": "北京大学",
        "major": "计算机科学",
        "grade": "大二",
        "interest_tags": ["编程", "数学建模"],
        "bio": "热爱编程",
    }
    resp = client.put("/api/v1/profile", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["university"] == "北京大学"
    assert data["major"] == "计算机科学"
    assert data["grade"] == "大二"
    assert data["interest_tags"] == ["编程", "数学建模"]
    assert data["bio"] == "热爱编程"


def test_put_profile_update_partial(client):
    """部分更新只修改已提交字段"""
    headers = _register_and_login(client)
    client.put("/api/v1/profile", json={
        "university": "清华大学",
        "major": "软件工程",
    }, headers=headers)

    # 只更新 major
    resp = client.put("/api/v1/profile", json={"major": "人工智能"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["university"] == "清华大学"  # 未变
    assert data["major"] == "人工智能"  # 已更新


def test_get_profile_after_update(client):
    """PUT 后 GET 返回最新数据"""
    headers = _register_and_login(client)
    client.put("/api/v1/profile", json={
        "university": "浙江大学",
        "interest_tags": ["英语", "写作"],
    }, headers=headers)

    resp = client.get("/api/v1/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["university"] == "浙江大学"
    assert data["interest_tags"] == ["英语", "写作"]


# --- 7.2 失败场景 ---

def test_get_profile_unauthorized(client):
    """未登录访问返回 401"""
    resp = client.get("/api/v1/profile")
    assert resp.status_code == 401


def test_put_profile_unauthorized(client):
    """未登录更新返回 401"""
    resp = client.put("/api/v1/profile", json={"university": "test"})
    assert resp.status_code == 401
