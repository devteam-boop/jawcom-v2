"""Application settings loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Central configuration for the JawCom backend.

    Values are read from environment variables, falling back to the
    backend `.env` file, then to the defaults declared here.
    """

    # Application
    PROJECT_NAME: str = "JawCom Backend"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # Database (PostgreSQL / Supabase, async via asyncpg)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Async PostgreSQL DSN, e.g. postgresql+asyncpg://user:pass@host:5432/db",
    )
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis (reserved for future workers / caching)
    REDIS_URL: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_POLL_INTERVAL: int = 30

    # Integrations (secrets loaded from environment)
    WHATSAPP_API_KEY: Optional[str] = Field(
        default=None, description="Meta WhatsApp Business API key",
    )
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = Field(
        default=None, description="Meta WhatsApp phone number ID",
    )
    WHATSAPP_ACCESS_TOKEN: Optional[str] = Field(
        default=None, description="Meta WhatsApp access token",
    )
    EMAIL_PROVIDER: str = Field(
        default="smtp", description="Email provider (smtp, sendgrid, …)",
    )
    EMAIL_API_KEY: Optional[str] = Field(
        default=None, description="Email provider API key",
    )
    EMAIL_SENDER: Optional[str] = Field(
        default=None, description="Default sender email address",
    )

    # Meta WhatsApp Cloud API (native provider — app/providers/meta/meta_provider.py)
    # Reuses WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID above; adds the
    # two fields those didn't cover.
    META_BUSINESS_ACCOUNT_ID: Optional[str] = Field(
        default=None, description="Meta WhatsApp Business Account ID (required for template status lookups)",
    )
    META_API_VERSION: str = Field(
        default="v21.0", description="Meta Graph API version used by MetaProvider",
    )
    META_WEBHOOK_VERIFY_TOKEN: Optional[str] = Field(
        default=None, description="Shared secret for Meta's GET webhook verification handshake (hub.verify_token)",
    )

    # Resend Email API (native provider — app/providers/resend/resend_provider.py)
    # Dedicated names (mirrors JAWIS_API_TOKEN vs JAWIS_API_KEY precedent);
    # ResendProvider falls back to EMAIL_API_KEY / EMAIL_SENDER if unset.
    RESEND_API_KEY: Optional[str] = Field(
        default=None, description="Resend API key (falls back to EMAIL_API_KEY if unset)",
    )
    RESEND_FROM_EMAIL: Optional[str] = Field(
        default=None, description="Default 'from' address for Resend (falls back to EMAIL_SENDER if unset)",
    )

    # AI Lead Assistant (Claude API — app/services/ai_lead_assistant_service.py)
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None, description="Anthropic API key for the AI Lead Assistant",
    )
    ANTHROPIC_MODEL: str = Field(
        default="claude-opus-4-8", description="Claude model used by the AI Lead Assistant",
    )

    # JAWIS
    JAWIS_BASE_URL: Optional[str] = Field(
        default=None, description="JAWIS API base URL, e.g. https://api.jawis.io",
    )
    JAWIS_API_KEY: Optional[str] = Field(
        default=None, description="JAWIS API authentication key",
    )
    JAWIS_API_TOKEN: Optional[str] = Field(
        default=None,
        description="JAWIS Communication API bearer token (Sprint-1 messages/*.send endpoints)",
    )
    JAWIS_WORKSPACE: Optional[str] = Field(
        default=None, description="JAWIS workspace / tenant ID",
    )
    JAWIS_LEAD_PROVIDER: str = Field(
        default="dummy", description="Lead provider backend: dummy or jawis",
    )
    JAWIS_CRM_PROVIDER: str = Field(
        default="dummy", description="CRM integration backend: dummy or jawis",
    )
    JAWIS_WHATSAPP_PROVIDER: str = Field(
        default="jawis", description="WhatsApp integration backend: dummy, jawis, or meta",
    )
    JAWIS_EMAIL_PROVIDER: str = Field(
        default="jawis", description="Email integration backend: dummy, jawis, or resend",
    )

    # CORS
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATABASE_URL", "REDIS_URL", mode="before")
    @classmethod
    def _empty_string_as_none(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, value: Optional[str]) -> Optional[str]:
        """Ensure the async asyncpg driver is used for plain postgres DSNs."""
        if value and value.startswith(("postgres://", "postgresql://")):
            scheme, _, rest = value.partition("://")
            return f"postgresql+asyncpg://{rest}"
        return value

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def cors_origins(self) -> list[str]:
        return self._split_csv(self.CORS_ORIGINS)

    @property
    def cors_allow_methods(self) -> list[str]:
        return self._split_csv(self.CORS_ALLOW_METHODS)

    @property
    def cors_allow_headers(self) -> list[str]:
        return self._split_csv(self.CORS_ALLOW_HEADERS)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
