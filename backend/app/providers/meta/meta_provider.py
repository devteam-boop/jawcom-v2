"""Meta (Facebook) WhatsApp Business Cloud API provider.

Completes the ``WhatsAppProvider`` abstraction with real Graph API calls.
Credentials come from the config dict passed at construction (the pattern
``ProviderRegistry.register_provider()`` already uses), falling back to
environment settings when the dict doesn't supply them — so provider
selection remains environment-driven even when instantiated with an empty
config (``MetaProvider({})``).

Not wired into ``IntegrationFactory``/``ExecutorFactory``/``ExecutionEngine``.
This is a standalone, ready-to-use provider implementation only — task
scope is "Build only provider implementations".

Delivery/read status is intentionally NOT implemented: the real WhatsApp
Cloud API has no polling endpoint for message status — it is only
delivered via configured webhooks, which are explicitly out of scope for
this task. ``get_message_status`` raises ``NotImplementedError`` rather
than faking a status.
"""

from typing import Dict, Any, Optional, List

import httpx

from ..base.whatsapp_provider import WhatsAppProvider
from ..base.communication_provider import MessageStatus, MessageType


class MetaProvider(WhatsAppProvider):
    """Meta (Facebook) WhatsApp Business Cloud API provider."""

    GRAPH_BASE_URL = "https://graph.facebook.com"

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Configuration dict with keys:
                - access_token: Meta access token (falls back to WHATSAPP_ACCESS_TOKEN)
                - phone_number_id: WhatsApp Business phone number ID (falls back to WHATSAPP_PHONE_NUMBER_ID)
                - business_account_id: Meta Business Account ID (falls back to META_BUSINESS_ACCOUNT_ID)
                - api_version: Graph API version (falls back to META_API_VERSION, default "v21.0")
        """
        super().__init__(config)
        from app.config.settings import get_settings
        settings = get_settings()

        self.access_token = config.get("access_token") or settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = config.get("phone_number_id") or settings.WHATSAPP_PHONE_NUMBER_ID
        self.business_account_id = config.get("business_account_id") or settings.META_BUSINESS_ACCOUNT_ID
        self.api_version = config.get("api_version") or settings.META_API_VERSION

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        """Whether enough credentials exist to send a message.

        Deliberately does not require ``business_account_id`` — that's only
        needed by ``get_template_status``, not by sending.
        """
        return bool(self.access_token and self.phone_number_id)

    async def send_message(
        self,
        recipient: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a plain-text WhatsApp message via the Graph API."""
        if not await self.validate_recipient(recipient):
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": "Invalid recipient phone number",
            }
        if not self.is_configured():
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": "MetaProvider not configured (missing access_token/phone_number_id)",
            }

        url = f"{self.GRAPH_BASE_URL}/{self.api_version}/{self.phone_number_id}/messages"
        body = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": message},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=self._headers(), json=body)
        except httpx.RequestError as exc:
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": f"Meta API unreachable: {exc}",
            }

        if response.status_code >= 400:
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": f"Meta API error {response.status_code}: {response.text}",
            }

        data = response.json()
        message_id = (data.get("messages") or [{}])[0].get("id")
        return {
            "provider_message_id": message_id,
            "status": MessageStatus.SENT.value,
            "provider": "meta",
            "channel": "whatsapp",
        }

    async def send_template_message(
        self,
        recipient: str,
        template_name: str,
        template_language: str,
        template_parameters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send an approved WhatsApp template message via the Graph API."""
        if not await self.validate_recipient(recipient):
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": "Invalid recipient phone number",
            }
        if not self.is_configured():
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": "MetaProvider not configured (missing access_token/phone_number_id)",
            }

        components = []
        if template_parameters:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in template_parameters],
            })

        url = f"{self.GRAPH_BASE_URL}/{self.api_version}/{self.phone_number_id}/messages"
        body = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": template_language},
                "components": components,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=self._headers(), json=body)
        except httpx.RequestError as exc:
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": f"Meta API unreachable: {exc}",
            }

        if response.status_code >= 400:
            return {
                "provider_message_id": None,
                "status": MessageStatus.FAILED.value,
                "error": f"Meta API error {response.status_code}: {response.text}",
            }

        data = response.json()
        message_id = (data.get("messages") or [{}])[0].get("id")
        return {
            "provider_message_id": message_id,
            "status": MessageStatus.SENT.value,
            "provider": "meta",
            "channel": "whatsapp",
            "template_name": template_name,
        }

    async def get_message_status(self, provider_message_id: str) -> MessageStatus:
        """Not implemented: the real WhatsApp Cloud API has no polling
        endpoint for delivery/read status — it is only delivered via
        configured webhooks, which are explicitly out of scope for this
        task ("Do not implement delivery/read webhooks yet")."""
        raise NotImplementedError(
            "Meta WhatsApp Cloud API does not support polling message status; "
            "delivery/read status is only available via webhooks (not yet implemented)."
        )

    async def get_template_status(self, template_name: str) -> str:
        """Look up a template's approval status via the Message Templates API.

        This is a real, legitimate polling endpoint (distinct from
        delivery/read tracking) — Meta does expose template approval status
        for querying, unlike message delivery status.
        """
        if not self.business_account_id:
            return "UNKNOWN"

        url = f"{self.GRAPH_BASE_URL}/{self.api_version}/{self.business_account_id}/message_templates"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    url, headers=self._headers(), params={"name": template_name},
                )
        except httpx.RequestError:
            return "UNKNOWN"

        if response.status_code >= 400:
            return "UNKNOWN"

        results = response.json().get("data") or []
        if not results:
            return "UNKNOWN"
        return results[0].get("status", "UNKNOWN")

    async def upload_media(self, media_url: str, media_type: str) -> str:
        """Download media from ``media_url`` and upload it to Meta, returning the media ID.

        Raises on failure (matches the ``-> str`` contract — there is no
        error-shaped return here, unlike send_message/send_template_message).
        """
        if not self.is_configured():
            raise RuntimeError("MetaProvider not configured (missing access_token/phone_number_id)")

        async with httpx.AsyncClient(timeout=30.0) as client:
            media_response = await client.get(media_url)
            media_response.raise_for_status()
            content = media_response.content

            filename = media_url.rsplit("/", 1)[-1] or "upload"
            upload_url = f"{self.GRAPH_BASE_URL}/{self.api_version}/{self.phone_number_id}/media"
            response = await client.post(
                upload_url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={"messaging_product": "whatsapp", "type": media_type},
                files={"file": (filename, content, media_type)},
            )
            response.raise_for_status()

        return response.json().get("id")
