"""Persist the owner's Google OAuth2 refresh token.

Resolution order:
1. GOOGLE_REFRESH_TOKEN env var / settings (best for production)
2. File on disk at api/.google_refresh_token.json (set by setup_calendar.py or OAuth callback)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

_TOKEN_PATH = Path(__file__).resolve().parent.parent.parent / ".google_refresh_token.json"


def save_refresh_token(refresh_token: str) -> None:
    """Write the refresh token to disk."""
    _TOKEN_PATH.write_text(json.dumps({"refresh_token": refresh_token}))
    log.info("Saved Google refresh token to %s", _TOKEN_PATH)


def load_refresh_token() -> str | None:
    """Load refresh token from env/config first, then file."""
    # 1. Check config/env var
    try:
        from app.config import get_settings
        token = get_settings().google_refresh_token
        if token:
            return token
    except Exception:
        pass

    # 2. Check file on disk
    if not _TOKEN_PATH.exists():
        return None
    try:
        data = json.loads(_TOKEN_PATH.read_text())
        return data.get("refresh_token")
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Could not load refresh token from file: %s", exc)
        return None
