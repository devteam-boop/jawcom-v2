"""Application settings loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import AliasChoices, Field, field_validator
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
    # validation_alias: Step 0 audit found the deployed .env uses
    # META_PHONE_NUMBER_ID / META_WABA_ACCESS_TOKEN / META_WABA_ID rather
    # than these field names — accepting both so the already-configured
    # production secrets are picked up without renaming them, while the
    # rest of the codebase keeps referring to the WHATSAPP_*/META_BUSINESS_*
    # attribute names.
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WHATSAPP_PHONE_NUMBER_ID", "META_PHONE_NUMBER_ID"),
        description="Meta WhatsApp phone number ID",
    )
    WHATSAPP_ACCESS_TOKEN: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WHATSAPP_ACCESS_TOKEN", "META_WABA_ACCESS_TOKEN"),
        description=(
            "Meta WhatsApp access token. Testing tokens expire every 24h and are "
            "rotated manually — MetaProvider reads this from os.environ directly "
            "at construction time rather than through this cached Settings "
            "singleton, so a rotated value is picked up without a process restart."
        ),
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
        default=None,
        validation_alias=AliasChoices("META_BUSINESS_ACCOUNT_ID", "META_WABA_ID", "WABA_ID"),
        description="Meta WhatsApp Business Account ID / WABA ID (required for template status lookups, sync, and submit)",
    )
    META_API_VERSION: str = Field(
        default="v21.0", description="Meta Graph API version used by MetaProvider",
    )
    META_WEBHOOK_VERIFY_TOKEN: Optional[str] = Field(
        default=None, description="Shared secret for Meta's GET webhook verification handshake (hub.verify_token)",
    )
    META_APP_SECRET: Optional[str] = Field(
        default=None,
        description=(
            "Meta App Secret — used to verify the X-Hub-Signature-256 header on "
            "inbound POST webhook deliveries before the body is trusted."
        ),
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

    # Gmail API (reply tracking — app/gmail_sync/). Existing OAuth credentials
    # (installed refresh token, not a fresh interactive consent flow).
    GOOGLE_CLIENT_ID: Optional[str] = Field(
        default=None, description="Google OAuth client ID (Gmail API reply sync)",
    )
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(
        default=None, description="Google OAuth client secret (Gmail API reply sync)",
    )
    GOOGLE_REFRESH_TOKEN: Optional[str] = Field(
        default=None, description="Google OAuth refresh token for the monitored Gmail inbox",
    )
    GMAIL_MONITOR_EMAIL: Optional[str] = Field(
        default=None, description="Gmail address being monitored for inbound replies",
    )
    EMAIL_SYNC_WEBHOOK_TOKEN: Optional[str] = Field(
        default=None, description="Shared secret required in X-Webhook-Token for POST /api/email-sync/run",
    )

    # JAWIS <-> JawCom hybrid communication (see backend/docs, JAWIS-side
    # COMMUNICATION_ENGINE=jawcom mode). Shared secret both directions:
    # JAWIS sends it as Authorization: Bearer <token> when calling JawCom's
    # /api/messages/*, /api/communication-events, /api/leads/*/journey/*;
    # JawCom sends it the same way when publishing to JAWIS_WEBHOOK_URL.
    JAWCOM_API_TOKEN: Optional[str] = Field(
        default=None, description="Shared bearer token for JAWIS<->JawCom hybrid communication auth",
    )

    # JawCom's own agent session auth (Phase 3, Task 1) — distinct from
    # JAWCOM_API_TOKEN above. This app has no per-user login system; this is
    # a deliberately minimal shared-workspace passcode, NOT a multi-user
    # auth system. A logged-in agent's session token is accepted (alongside
    # JAWCOM_API_TOKEN) on /api/messages/* ONLY — never on
    # /api/leads/*/journey/* or any other JAWIS-protected route, so a leaked
    # agent session can never be used to impersonate JAWIS. See
    # app/core/session_auth.py.
    JAWCOM_APP_PASSWORD: Optional[str] = Field(
        default=None, description="Shared passcode agents use to log in at /api/auth/login",
    )
    JAWCOM_SESSION_SECRET: Optional[str] = Field(
        default=None, description="HMAC signing key for agent session tokens issued by /api/auth/login",
    )
    JAWIS_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="JAWIS's webhook receiver — JawCom POSTs email_sent/whatsapp_sent/delivered/read/clicked/"
                    "replied/failed communication_events here (sole JawCom->JAWIS sync mechanism); event_type "
                    "values match CommunicationEventType, not generic sent/opened labels",
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
