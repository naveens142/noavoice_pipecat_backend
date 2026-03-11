"""
Application settings — single source of truth for all configuration.

All sensitive values come from environment variables / .env file.
Validation runs at startup — app fails fast if required vars are missing.

Generate SECRET_KEY with:
    python -c "import secrets; print(secrets.token_hex(64))"
"""
import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator, computed_field
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):

    # ── App ───────────────────────────────────────────────────────────────
    APP_NAME: str = "NoaVoiceAI"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "production"

    # ── Cal.com V2 ────────────────────────────────────────────────────────
    CALCOM_API_KEY: str
    CALCOM_EVENT_TYPE_ID: int
    CALCOM_BASE_URL: str = "https://api.cal.com/v2"
    CALCOM_API_VERSION: str = "2024-08-13"

    # ── Neon PostgreSQL ───────────────────────────────────────────────────
    DATABASE_URL: str
    DB_SCHEMA: str = "noavoice_ns"

    # ── External APIs ─────────────────────────────────────────────────────
    OPENWEATHER_API_KEY: str

    # ── Security / JWT ────────────────────────────────────────────────────
    # Generate with: python -c "import secrets; print(secrets.token_hex(64))"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # ── Google OAuth / OIDC ───────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Standard Google OIDC discovery URL — never changes
    GOOGLE_DISCOVERY_URL: str = "https://accounts.google.com/.well-known/openid-configuration"

    # ── Redis (CSRF state + nonce storage) ────────────────────────────────
    REDIS_URL:str

    # ── Frontend ──────────────────────────────────────────────────────────
    FRONTEND_URL: str= "http://localhost:5173"

    # -----------Pipecat Agent-----------------------------------------------------
    AGENT_BASE_URL: str = "http://localhost:7860"

    # TWILIO
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str 

    # Your public URL (use ngrok for local dev)
    BASE_URL: str = "https://incretory-unerodable-tiffani.ngrok-free.dev"

    # Knowledge Base Configuration - Absolute path based on actual file location
    @computed_field  # type: ignore[misc]
    @property
    def kb_upload_dir(self) -> str:
        """Calculate absolute path for KB uploads based on settings file location."""
        settings_dir = os.path.dirname(os.path.abspath(__file__))  # /path/to/app/config
        project_root = os.path.dirname(os.path.dirname(settings_dir))  # /path/to/project
        kb_dir = os.path.join(project_root, 'app', 'knowledge_base')
        # Fallback to /tmp for production (Render)
        if not os.path.exists(kb_dir) and self.ENVIRONMENT == "production":
            kb_dir = "/tmp/knowledge_base"
            os.makedirs(kb_dir, exist_ok=True)
        return kb_dir
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Agent validation
    VALID_TIMEZONES: list[str] = [
        'America/Detroit', 'America/New_York', 'America/Los_Angeles',
        'America/Chicago', 'Europe/London', 'Europe/Paris',
        'Asia/Tokyo', 'Asia/Dubai', 'UTC'
    ]
    
    VALID_LANGUAGES: list[str] = ['EN', 'ES', 'FR', 'DE', 'JA', 'ZH']

    # ─────────────────────────────────────────────────────────────────────
    # Validators
    # ─────────────────────────────────────────────────────────────────────

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """
        Enforce minimum entropy — 64 chars = 256 bits minimum.
        App refuses to start with a weak secret key.
        """
        if len(v) < 64:
            raise ValueError(
                "SECRET_KEY must be at least 64 characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(64))\""
            )
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Stricter checks when running in production."""
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
            if "localhost" in self.GOOGLE_REDIRECT_URI:
                raise ValueError("GOOGLE_REDIRECT_URI cannot use localhost in production")
            if "localhost" in self.FRONTEND_URL:
                raise ValueError("FRONTEND_URL cannot use localhost in production")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True
        populate_by_name = True


# ── Single cached instance ────────────────────────────────────────────────────
# lru_cache ensures .env is parsed only once at startup.
# Use get_settings() in FastAPI Depends() for testability.

@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Convenience alias — your existing imports still work unchanged:
#   from app.config.settings import settings   ✅ still works
settings = get_settings()