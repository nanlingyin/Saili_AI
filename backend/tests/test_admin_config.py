from pathlib import Path


def _admin_headers(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_api_provider_config_read_and_update(client):
    headers = _admin_headers(client)

    read_resp = client.get("/api/v1/admin/config/api-providers", headers=headers)
    assert read_resp.status_code == 200
    read_body = read_resp.json()
    assert "providers" in read_body
    assert "ai_extraction" in read_body["providers"]

    payload = read_body
    payload["providers"]["ai_extraction"]["enabled"] = True
    payload["providers"]["ai_extraction"]["base_url"] = "https://api.example.com/extract"
    payload["providers"]["ai_extraction"]["model"] = "demo-model"
    payload["providers"]["ai_extraction"]["api_key"] = "secret-123456"
    payload["providers"]["ingestion"]["stable_source_path"] = "data/custom-source.json"
    payload["providers"]["ingestion"]["failure_threshold"] = 5

    save_resp = client.put(
        "/api/v1/admin/config/api-providers",
        headers=headers,
        json=payload,
    )
    assert save_resp.status_code == 200
    save_body = save_resp.json()
    assert save_body["providers"]["ai_extraction"]["api_key"].startswith("se")
    assert "********" in save_body["providers"]["ai_extraction"]["api_key"]
    assert save_body["providers"]["ingestion"]["failure_threshold"] == 5

    keep_key_payload = save_body
    keep_key_payload["providers"]["ai_extraction"]["api_key"] = ""
    keep_key_payload["providers"]["ingestion"]["failure_threshold"] = 6
    keep_key_resp = client.put(
        "/api/v1/admin/config/api-providers",
        headers=headers,
        json=keep_key_payload,
    )
    assert keep_key_resp.status_code == 200
    assert keep_key_resp.json()["providers"]["ingestion"]["failure_threshold"] == 6


def test_api_provider_config_file_persisted(client):
    headers = _admin_headers(client)
    payload = client.get("/api/v1/admin/config/api-providers", headers=headers).json()
    payload["providers"]["ingestion"]["fallback_source_path"] = "data/fallback-custom.json"
    payload["providers"]["auth"]["access_token_expire_minutes"] = 180

    save_resp = client.put(
        "/api/v1/admin/config/api-providers",
        headers=headers,
        json=payload,
    )
    assert save_resp.status_code == 200

    import os

    config_path = Path(os.environ["API_PROVIDER_CONFIG_PATH"])
    assert config_path.exists()
    text = config_path.read_text(encoding="utf-8")
    assert "fallback-custom.json" in text
    assert "access_token_expire_minutes: 180" in text
