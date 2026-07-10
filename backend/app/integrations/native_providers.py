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

These integrations do NOT resolve the recipient themselves — no
LeadProviderFactory, no get_lead_context(), no get_lead(), no JAWIS call of
any kind. The caller (app/api/message_routes.py, the Communication Engine)
resolves recipient_email/recipient_phone/recipient_name exactly once and
passes them in the payload. This class only talks to Resend/Meta.

app/execution/executors/send_email_executor.py and send_whatsapp_executor.py
(Journey Engine) call IntegrationFactory.get("email")/get("whatsapp") — the
alias keys, which resolve to THIS module's classes only if an operator sets
JAWIS_EMAIL_PROVIDER=resend / JAWIS_WHATSAPP_PROVIDER=meta (default stays
"jawis", i.e. jawis_communication.py's classes). Those two executors already
include recipient_email/recipient_phone/recipient_name in their payload
(sourced from exec_ctx.lead — data the engine already resolved for the
node, no extra lookup added), so this module works correctly under either
alias target without performing any lead lookup of its own.

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

        # Recipient is resolved exactly once by the caller and passed in —
        # this integration performs no lead lookup of its own.
        phone = payload.get("recipient_phone")
        if not phone:
            raise NativeProviderError("No phone number available for recipient")

        variables = payload.get("variables") or {}
        result = await provider.send_template_message(
            recipient=phone.lstrip("+"),
            template_name=payload.get("template_name") or "",
            # Optional — absent for every existing caller (Journey Engine's
            # send_whatsapp_executor.py never sets this key), so this stays
            # "en_US" exactly as before unless a caller opts in (WhatsApp
            # Template Management Phase 1, Feature 5).
            template_language=payload.get("language") or "en_US",
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

        # Recipient is resolved exactly once by the caller and passed in —
        # this integration performs no lead lookup of its own.
        email_address = payload.get("recipient_email")
        if not email_address:
            raise NativeProviderError("No email address available for recipient")

        result = await provider.send_email(
            recipient=email_address,
            subject=payload.get("subject") or "",
            body=payload.get("text") or "",
            html_body=payload.get("html"),
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
