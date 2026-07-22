"""Application configuration via Pydantic Settings.

All secrets and tunables come from environment variables / ``.env``. The same
settings object drives both LOCAL_MVP and FULL — only values change.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = apps/backend/app/core/config.py -> parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent.parent


class AppMode(str, Enum):
    LOCAL_MVP = "LOCAL_MVP"
    FULL = "FULL"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_env: str = "development"
    app_mode: AppMode = AppMode.LOCAL_MVP
    app_timezone: str = "Europe/Chisinau"
    log_level: str = "INFO"
    log_json: bool = False

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_use_webhook: bool = False
    initial_owner_telegram_id: int | None = None

    # Default device (LOCAL_MVP single-device bootstrap; matches the agent's .env)
    agent_device_id: str = "main-camp-speakers"
    agent_device_token: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    redis_url: str = ""

    # Public URLs
    public_base_url: str = ""
    mini_app_url: str = ""
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    # Security
    secret_key: str = "change-me-in-production-please-32chars-min"
    access_token_ttl_seconds: int = 3600
    initdata_max_age_seconds: int = 86400

    # Volume policy
    default_volume: int = 60
    max_safe_volume: int = 80
    absolute_max_volume: int = 100
    volume_step: int = 5

    # Timing / reliability
    heartbeat_interval_seconds: int = 5
    device_offline_after_seconds: int = 20
    command_ttl_seconds: int = 20
    schedule_grace_period_seconds: int = 60
    callback_ttl_seconds: int = 120
    resume_after_restart: bool = False

    # Uploads
    music_cache_path: str = "./storage/music"
    max_upload_size_mb: int = 50

    # Feature flags
    tts_enabled: bool = False
    mini_app_enabled: bool = True

    @field_validator("cors_origins")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def music_dir(self) -> Path:
        p = Path(self.music_cache_path)
        if not p.is_absolute():
            p = REPO_ROOT / p
        return p

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def sync_database_url(self) -> str:
        """Blocking driver URL (used by Alembic)."""
        url = self.database_url
        return (
            url.replace("+aiosqlite", "")
            .replace("+asyncpg", "+psycopg2")
            .replace("sqlite:///", "sqlite:///")
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
