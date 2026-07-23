"""Integration configuration — loaded from application settings.

All secrets (API keys, tokens) are sourced from environment variables
via the central ``Settings`` object.  No hardcoded credentials.
"""

from typing import Optional

from app.config.settings import get_settings


class IntegrationConfig:
    """Read‑only configuration for all integrations.

    Usage::

        cfg = IntegrationConfig()
        if cfg.whatsapp_api_key:
            # configured
    """

    def __init__(self) -> None:
        settings = get_settings()

        # ── WhatsApp ───────────────────────────────────────────────
        self.whatsapp_api_key: Optional[str] = settings.WHATSAPP_API_KEY
        self.whatsapp_phone_number_id: Optional[str] = settings.WHATSAPP_PHONE_NUMBER_ID
        self.whatsapp_access_token: Optional[str] = settings.WHATSAPP_ACCESS_TOKEN

        # ── Email ──────────────────────────────────────────────────
        self.email_provider: str = settings.EMAIL_PROVIDER
        self.email_api_key: Optional[str] = settings.EMAIL_API_KEY
        self.email_sender: Optional[str] = settings.EMAIL_SENDER

        # ── JAWIS ──────────────────────────────────────────────────
        self.jawis_base_url: Optional[str] = settings.JAWIS_BASE_URL
        self.jawis_api_key: Optional[str] = settings.JAWIS_API_KEY
        self.jawis_api_token: Optional[str] = settings.JAWIS_API_TOKEN
        self.jawis_workspace: Optional[str] = settings.JAWIS_WORKSPACE
        self.jawis_lead_provider: str = settings.JAWIS_LEAD_PROVIDER
        self.jawis_crm_provider: str = settings.JAWIS_CRM_PROVIDER
        self.jawis_notification_endpoint: str = settings.JAWIS_NOTIFICATION_ENDPOINT

    def to_dict(self) -> dict:
        """Return all fields as a dict (safe for logging — masks secrets)."""
        return {
            "whatsapp_phone_number_id": self.whatsapp_phone_number_id,
            "email_provider": self.email_provider,
            "email_sender": self.email_sender,
            "whatsapp_api_key": "***" if self.whatsapp_api_key else None,
            "whatsapp_access_token": "***" if self.whatsapp_access_token else None,
            "email_api_key": "***" if self.email_api_key else None,
            "jawis_base_url": self.jawis_base_url,
            "jawis_workspace": self.jawis_workspace,
            "jawis_lead_provider": self.jawis_lead_provider,
            "jawis_crm_provider": self.jawis_crm_provider,
            "jawis_notification_endpoint": self.jawis_notification_endpoint,
            "jawis_api_key": "***" if self.jawis_api_key else None,
            "jawis_api_token": "***" if self.jawis_api_token else None,
        }
