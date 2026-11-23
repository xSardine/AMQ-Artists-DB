"""Small configuration reader; process environment takes precedence over .env."""

import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def setting(name: str, default: str = "") -> str:
    if name in os.environ:
        return os.environ[name]
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.strip().partition("=")
            if separator and not key.startswith("#") and key.strip() == name:
                return value.strip().strip("\"'")
    return default


def frontend_origins() -> list[str]:
    return [
        origin.strip().rstrip("/")
        for origin in setting(
            "FRONTEND_ORIGINS", "https://anisongdb.com,http://localhost:4200,http://127.0.0.1:4200"
        ).split(",")
        if origin.strip()
    ]
