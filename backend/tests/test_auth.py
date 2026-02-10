
def test_register_and_login(client):
    payload = {
        "username": "user1",
        "email": "user1@example.com",
        "password": "pass1234",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "user1", "password": "pass1234"},
    )
    assert login.status_code == 200
    data = login.json()
    assert data["access_token"]