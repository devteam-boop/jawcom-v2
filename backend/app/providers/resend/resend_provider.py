"""Resend (resend.com) transactional email provider.

Completes the ``EmailProvider`` abstraction with real Resend API calls.
Credentials come from the config dict passed at construction, falling back
to environment settings (RESEND_API_KEY/RESEND_FROM_EMAIL, then the
generic EMAIL_API_KEY/EMAIL_SENDER) — provider selection remains
environment-driven even with an empty config dict.

Not wired into ``IntegrationFactory``/``ExecutorFactory``/``ExecutionEngine``.
Standalone, ready-to-use provider implementation only — task scope is
"Build only provider implementations".

``send_template_email`` raises ``NotImplementedError``: Resend has no
server-side stored-template API (unlike SendGrid) — JawCom's own
TemplateRendererService already resolves ``{{variable}}`` templates before
calling ``send_email()``, so this method is unreachable in practice and
exists only to satisfy the ``EmailProvider`` abstract contract.

``get_message_status``/``get_bounce_status`` use Resend's real
``GET /emails/{id}`` polling endpoint (not a webhook), so delivery/read
webhooks remain out of scope per this task while still giving a real,
best-effort status snapshot.
"""

from typing import Dict, Any, Optional, List

import httpx

from ..base.email_provider import EmailProvider
from ..base.communication_provider import MessageStatus, MessageType


class ResendProvider(EmailProvider):
    """Resend transactional email provider."""

    API_BASE_URL = "https://api.resend.com"

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Configuration dict with keys:
                - api_key: Resend API key (falls back to RESEND_API_KEY, then EMAIL_API_KEY)
                - from_email: Default sender address (falls back to RESEND_FROM_EMAIL, then EMAIL_SENDER)
        """
        super().__init__(config)
        from app.config.settings import get_settings
        settings = get_settings()

        self.api_key = config.get("api_key") or settings.RESEND_API_KEY or settings.EMAIL_API_KEY
        self.from_email = config.get("from_email") or settings.RESEND_FROM_EMAIL or settings.EMAIL_SENDER

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        return bool(self.api_key and self.from_email)

    async def send_message(
        self,
        recipient: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generic CommunicationProvider entrypoint — for email this is a
        plain-text send with an optional subject supplied via metadata."""
        subject = (metadata or {}).get("subject", "")
        return await self.send_email(recipient, subject, message)

    async def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if not await self.validate_recipient(recipient):
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": "Invalid recipient email address",
            }
        if not self.is_configured():
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": "ResendProvider not configured (missing api_key/from_email)",
            }

        payload: Dict[str, Any] = {
            "from": self.from_email,
            "to": [recipient],
            "subject": subject,
            "text": body,
        }
        if html_body:
            payload["html"] = html_body
        if attachments:
            payload["attachments"] = attachments

        url = f"{self.API_BASE_URL}/emails"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=self._headers(), json=payload)
        except httpx.RequestError as exc:
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": f"Resend API unreachable: {exc}",
            }

        if response.status_code >= 400:
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": f"Resend API error {response.status_code}: {response.text}",
            }

        data = response.json()
        return {
            "provider_message_id": data.get("id"),
            "status": MessageStatus.SENT.value,
            "provider": "resend",
            "channel": "email",
        }

    async def send_template_email(
        self,
        recipient: str,
        template_id: str,
        template_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError(
            "Resend has no server-side stored-template API. JawCom resolves "
            "{{variable}} templates via TemplateRendererService before calling "
            "send_email() — this method exists only to satisfy the EmailProvider contract."
        )

    async def _fetch_email(self, provider_message_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.API_BASE_URL}/emails/{provider_message_id}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self._headers())
        except httpx.RequestError:
            return None
        if response.status_code >= 400:
            return None
        return response.json()

    async def get_message_status(self, provider_message_id: str) -> MessageStatus:
        """Best-effort status snapshot via Resend's GET /emails/{id} (a real
        poll, not a webhook). Real-time delivered/opened/clicked tracking
        beyond this snapshot requires webhooks — deferred per this task."""
        data = await self._fetch_email(provider_message_id)
        if not data:
            return MessageStatus.FAILED

        last_event = (data.get("last_event") or "").lower()
        return {
            "delivered": MessageStatus.DELIVERED,
            "sent": MessageStatus.SENT,
            "bounced": MessageStatus.FAILED,
            "complained": MessageStatus.FAILED,
        }.get(last_event, MessageStatus.PENDING)

    async def get_bounce_status(self, provider_message_id: str) -> Optional[str]:
        data = await self._fetch_email(provider_message_id)
        if not data:
            return None
        last_event = (data.get("last_event") or "").lower()
        return last_event if last_event in ("bounced", "complained") else None
