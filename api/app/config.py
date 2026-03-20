from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ──────────────────────────────────────────────────────────────
    port: int = 8080
    environment: Literal["development", "production"] = "development"
    build_sha: str = "local-dev"
    allowed_origin: str = "http://localhost:3000"
    timezone: str = "America/Los_Angeles"

    # ── Content ─────────────────────────────────────────────────────────────
    content_dir: str = "../content"

    # ── Google / Gemini ──────────────────────────────────────────────────────
    google_api_key: str = ""
    google_genai_use_vertexai: bool = False
    # Chat model – Gemini 3.1 Pro preview (latest available)
    chat_model: str = "gemini-3.1-pro-preview"
    # Fast/cheap model
    fast_model: str = "gemini-3.1-flash-lite-preview"

    # ── Google OAuth2 ────────────────────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8080/auth/google/callback"
    # Comma-separated list of emails that get workspace (owner) access
    owner_emails: str = "jaiadityarathore@gmail.com"
    # Secret for signing JWT session tokens
    jwt_secret: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # ── Rate Limiting ────────────────────────────────────────────────────────
    chat_rate_limit: int = 60
    chat_rate_window: int = 300  # seconds
    action_rate_limit: int = 5
    action_rate_window: int = 600  # seconds

    # ── Timeouts ─────────────────────────────────────────────────────────────
    request_timeout: int = 30  # seconds
    sse_timeout: int = 300  # seconds (5 min)

    # ── SMTP (Feedback) ──────────────────────────────────────────────────────
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@jairathore.com"
    feedback_email: str = "jaiadityarathore@gmail.com"

    @field_validator("owner_emails", mode="before")
    @classmethod
    def strip_owner_emails(cls, v: str) -> str:
        return v.strip()

    @property
    def owner_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.owner_emails.split(",") if e.strip()}

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
