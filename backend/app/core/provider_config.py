import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AI_API_BASE_URL,
    AI_API_KEY,
    AI_API_MODEL,
    AI_API_TIMEOUT_SECONDS,
    API_PROVIDER_CONFIG_PATH,
    FALLBACK_SOURCE_PATH,
    INGEST_FAILURE_THRESHOLD,
    INGEST_INTERVAL_SECONDS,
    STABLE_SOURCE_PATH,
)

_LOCK = threading.Lock()
_MASK = "********"


def _config_path() -> Path:
    return Path(API_PROVIDER_CONFIG_PATH)


def _default_config() -> dict[str, Any]:
    return {
        "version": 1,
        "providers": {
            "ai_extraction": {
                "enabled": False,
                "base_url": "",
                "model": "",
                "api_key": "",
                "timeout_seconds": AI_API_TIMEOUT_SECONDS,
            },
            "ingestion": {
                "stable_source_path": STABLE_SOURCE_PATH,
                "fallback_source_path": FALLBACK_SOURCE_PATH,
                "failure_threshold": INGEST_FAILURE_THRESHOLD,
                "interval_seconds": INGEST_INTERVAL_SECONDS,
            },
            "auth": {
                "access_token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
            },
        },
    }


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return _MASK
    return f"{value[:2]}{_MASK}{value[-2:]}"


def _as_int(value: Any, default: int, minimum: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < minimum:
        return default
    return parsed


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    defaults = _default_config()
    providers = payload.get("providers") or {}
    ai = providers.get("ai_extraction") or {}
    ingestion = providers.get("ingestion") or {}
    auth = providers.get("auth") or {}

    return {
        "version": _as_int(payload.get("version"), defaults["version"]),
        "providers": {
            "ai_extraction": {
                "enabled": bool(ai.get("enabled", defaults["providers"]["ai_extraction"]["enabled"])),
                "base_url": str(ai.get("base_url", defaults["providers"]["ai_extraction"]["base_url"]) or "").strip(),
                "model": str(ai.get("model", defaults["providers"]["ai_extraction"]["model"]) or "").strip(),
                "api_key": str(ai.get("api_key", defaults["providers"]["ai_extraction"]["api_key"]) or "").strip(),
                "timeout_seconds": _as_int(
                    ai.get("timeout_seconds"),
                    defaults["providers"]["ai_extraction"]["timeout_seconds"],
                ),
            },
            "ingestion": {
                "stable_source_path": str(
                    ingestion.get(
                        "stable_source_path",
                        defaults["providers"]["ingestion"]["stable_source_path"],
                    )
                    or defaults["providers"]["ingestion"]["stable_source_path"]
                ).strip(),
                "fallback_source_path": str(
                    ingestion.get(
                        "fallback_source_path",
                        defaults["providers"]["ingestion"]["fallback_source_path"],
                    )
                    or defaults["providers"]["ingestion"]["fallback_source_path"]
                ).strip(),
                "failure_threshold": _as_int(
                    ingestion.get("failure_threshold"),
                    defaults["providers"]["ingestion"]["failure_threshold"],
                ),
                "interval_seconds": _as_int(
                    ingestion.get("interval_seconds"),
                    defaults["providers"]["ingestion"]["interval_seconds"],
                ),
            },
            "auth": {
                "access_token_expire_minutes": _as_int(
                    auth.get("access_token_expire_minutes"),
                    defaults["providers"]["auth"]["access_token_expire_minutes"],
                )
            },
        },
    }


def ensure_provider_config_file() -> None:
    path = _config_path()
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _default_config()
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def load_provider_config(mask_secrets: bool = False) -> dict[str, Any]:
    ensure_provider_config_file()
    path = _config_path()
    with _LOCK:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raw = {}
    payload = _normalize(raw)
    if mask_secrets:
        masked = deepcopy(payload)
        secret = masked["providers"]["ai_extraction"].get("api_key", "")
        masked["providers"]["ai_extraction"]["api_key"] = _mask_secret(secret)
        return masked
    return payload


def save_provider_config(updated: dict[str, Any]) -> dict[str, Any]:
    current = load_provider_config(mask_secrets=False)
    normalized = _normalize(updated)
    existing_key = current["providers"]["ai_extraction"]["api_key"]
    incoming_key = normalized["providers"]["ai_extraction"]["api_key"]
    if not incoming_key or incoming_key == _MASK or incoming_key.startswith("*"):
        normalized["providers"]["ai_extraction"]["api_key"] = existing_key

    path = _config_path()
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f"{path.suffix}.tmp")
        tmp.write_text(
            yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        tmp.replace(path)
    return load_provider_config(mask_secrets=True)


def get_runtime_ai_config() -> dict[str, Any]:
    payload = load_provider_config(mask_secrets=False)
    ai = payload["providers"]["ai_extraction"]
    base_url = ai.get("base_url") or AI_API_BASE_URL
    model = ai.get("model") or AI_API_MODEL
    api_key = ai.get("api_key") or AI_API_KEY
    timeout_seconds = _as_int(ai.get("timeout_seconds"), AI_API_TIMEOUT_SECONDS)
    enabled = bool(ai.get("enabled")) and bool(base_url and model and api_key)
    return {
        "enabled": enabled,
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
        "timeout_seconds": timeout_seconds,
    }


def get_runtime_ingestion_config() -> dict[str, Any]:
    payload = load_provider_config(mask_secrets=False)
    ingestion = payload["providers"]["ingestion"]
    return {
        "stable_source_path": ingestion.get("stable_source_path") or STABLE_SOURCE_PATH,
        "fallback_source_path": ingestion.get("fallback_source_path") or FALLBACK_SOURCE_PATH,
        "failure_threshold": _as_int(
            ingestion.get("failure_threshold"),
            INGEST_FAILURE_THRESHOLD,
        ),
        "interval_seconds": _as_int(
            ingestion.get("interval_seconds"),
            INGEST_INTERVAL_SECONDS,
        ),
    }


def get_runtime_auth_config() -> dict[str, Any]:
    payload = load_provider_config(mask_secrets=False)
    auth = payload["providers"].get("auth", {})
    return {
        "access_token_expire_minutes": _as_int(
            auth.get("access_token_expire_minutes"),
            ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
    }
