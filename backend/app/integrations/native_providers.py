"""Native provider integrations — Meta Cloud API (WhatsApp) and Resend (Email).

Wraps ``app/providers/`` (``MetaProvider``, ``ResendProvider``) behind the
``BaseIntegration`` interface, resolved through the *existing*
``ProviderRegistry`` (``app/providers/registry/provider_registry.py``) —
not instantiated directly — so that registry finally has a live caller
instead of being dormant.

Registered as ``"whatsapp_meta"`` / ``"email_resend"``. The ``"whatsapp"``/
``"email"`` aliases only resolve here when ``JAWIS_WHATSAPP_PROVIDER=meta``
/ ``JAWIS_EMAIL_PROVIDER=resend`` (see ``factory.py``) — default stays
JAWIS, unchanged.

Executors pass only ``{"recipient": lead_id, ...}`` (unchanged — no
execution logic changes). Unlike JAWIS, Meta/Resend need an actual phone
number / email address, so this integration resolves it itself via the
existing ``LeadProviderFactory`` — the same seam the engine already uses,
not a new one.

Raises ``NativeProviderError`` on failure — matching
``JawisCommunicationIntegration``'s convention (ADR-017) — so switching
providers via env var doesn't silently change failure semantics from
"raise -> failed node" to "success=True regardless".
"""

import logging
from typing import Any, Dict

from .base import BaseIntegration
from app.providers import provider_registry, Channel
from app.providers.meta.meta_provider import MetaProvider
from app.providers.resend.resend_provider import ResendProvider
from app.execution.providers import LeadProviderFactory

logger = logging.getLogger(__name__)


class NativeProviderError(Exception):
    """Raised when a native (Meta/Resend) provider send fails."""


# Register with the existing ProviderRegistry — previously nothing in the
# live app ever called it. Config is intentionally empty: both provider
# classes self-configure from environment settings (see app/providers/).
provider_registry.register_provider(Channel.WHATSAPP, MetaProvider, {})
provider_registry.register_provider(Channel.EMAIL, ResendProvider, {})


class MetaWhatsAppIntegration(BaseIntegration):
    """WhatsApp send via the real Meta Cloud API, resolved through ProviderRegistry."""

    @property
    def name(self) -> str:
        return "whatsapp_meta"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        provider = provider_registry.get_whatsapp_provider()
        if provider is None:
            raise NativeProviderError("Meta WhatsApp provider not registered")

        lead_id = payload.get("recipient")
        lead_context = await LeadProviderFactory.get_provider().get_lead_context(int(lead_id))
        phone = (lead_context.get("lead") or {}).get("phone")
        if not phone:
            raise NativeProviderError(f"No phone number available for lead {lead_id}")

        variables = payload.get("variables") or {}
        result = await provider.send_template_message(
            recipient=phone.lstrip("+"),
            template_name=payload.get("template_name") or "",
            template_language="en_US",
            template_parameters=list(variables.values()) if variables else None,
        )

        if result.get("status") == "failed":
            raise NativeProviderError(result.get("error") or "Meta WhatsApp send failed")

        # Alias for ExecutionEngine._record_communication_event(), which reads
        # payload["provider_response"]["message_id"] (the key JAWIS's response
        # already uses) to populate CommunicationEvent.provider_message_id.
        # Additive only — does not change any existing key, and the engine
        # itself is not touched.
        result["message_id"] = result.get("provider_message_id")
        return result

    async def health(self) -> Dict[str, Any]:
        provider = provider_registry.get_whatsapp_provider()
        configured = bool(provider and provider.is_configured())
        return {"status": "healthy" if configured else "unconfigured", "name": self.name, "configured": configured}


class ResendEmailIntegration(BaseIntegration):
    """Email send via the real Resend API, resolved through ProviderRegistry."""

    @property
    def name(self) -> str:
        return "email_resend"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        provider = provider_registry.get_email_provider()
        if provider is None:
            raise NativeProviderError("Resend email provider not registered")

        lead_id = payload.get("recipient")
        lead_context = await LeadProviderFactory.get_provider().get_lead_context(int(lead_id))
        email_address = (lead_context.get("lead") or {}).get("email")
        if not email_address:
            raise NativeProviderError(f"No email address available for lead {lead_id}")

        result = await provider.send_email(
            recipient=email_address,
            subject=payload.get("subject") or "",
            body=payload.get("content") or "",
        )

        if result.get("status") == "failed":
            raise NativeProviderError(result.get("error") or "Resend email send failed")

        # Same alias as MetaWhatsAppIntegration.execute() — see comment there.
        result["message_id"] = result.get("provider_message_id")
        return result

    async def health(self) -> Dict[str, Any]:
        provider = provider_registry.get_email_provider()
        configured = bool(provider and provider.is_configured())
        return {"status": "healthy" if configured else "unconfigured", "name": self.name, "configured": configured}
