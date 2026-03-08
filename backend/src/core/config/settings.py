"""Application settings loaded from environment variables via pydantic-settings."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class AIProvider(str, Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"


class LogFormat(str, Enum):
    JSON = "json"
    TEXT = "text"


class Settings(BaseSettings):
    """All application configuration. Values are read from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_env: AppEnv = AppEnv.DEVELOPMENT
    app_debug: bool = False
    app_secret_key: str = "change-me-in-production"

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str = "sqlite+aiosqlite:///./news.db"

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # -------------------------------------------------------------------------
    # AI Provider
    # -------------------------------------------------------------------------
    ai_provider: AIProvider = AIProvider.GEMINI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_fallback: bool = True   # fall back to ollama when gemini rate-limits

    # -------------------------------------------------------------------------
    # Feed collection
    # -------------------------------------------------------------------------
    default_fetch_interval: int = Field(default=60, ge=1)  # minutes

    # -------------------------------------------------------------------------
    # Email / SMTP
    # -------------------------------------------------------------------------
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    alert_email: str = ""
    alert_rate_limit_per_hour: int = 1
    digest_time: str = "08:00"   # HH:MM UTC

    # -------------------------------------------------------------------------
    # Celery
    # -------------------------------------------------------------------------
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    log_format: LogFormat = LogFormat.JSON

    # -------------------------------------------------------------------------
    # Cache TTLs (seconds)
    # -------------------------------------------------------------------------
    cache_ttl_feed_response: int = 3600      # 1 hour
    cache_ttl_ai_result: int = 86400         # 24 hours
    cache_ttl_article_list: int = 300        # 5 minutes

    @field_validator("app_secret_key")
    @classmethod
    def secret_key_must_be_set_in_production(cls, v: str, info: object) -> str:
        """Warn if secret key is not changed in production."""
        return v

    @property
    def is_testing(self) -> bool:
        return self.app_env == AppEnv.TESTING

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance. Use this everywhere."""
    return Settings()
