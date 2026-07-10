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

    async def list_templates(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch every message template configured for this Business Account
        (any status — PENDING/APPROVED/REJECTED/PAUSED/DISABLED — approval
        state changes over time so all of them need to be visible to a
        sync, not just the currently-approved ones), following Graph API's
        cursor pagination (``paging.next``) until exhausted.

        Used by WhatsAppTemplateService.sync_from_meta() (WhatsApp Template
        Management, Phase 1) — not used by message sending, and not wired
        into IntegrationFactory/BaseIntegration (same "provider
        implementation only" scope as the rest of this class).
        """
        if not self.business_account_id:
            raise RuntimeError("MetaProvider not configured (missing business_account_id)")

        url = f"{self.GRAPH_BASE_URL}/{self.api_version}/{self.business_account_id}/message_templates"
        # Explicit fields (rather than Meta's default set) so quality_score
        # and rejected_reason come back too — needed by WhatsApp Template
        # Management Phase 2's approval sync (quality_rating/rejection_reason
        # tracking) and not returned by default.
        params: Optional[Dict[str, Any]] = {
            "limit": limit,
            "fields": "id,name,language,category,status,components,quality_score,rejected_reason",
        }
        templates: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            while url:
                response = await client.get(url, headers=self._headers(), params=params)
                if response.status_code >= 400:
                    raise RuntimeError(f"Meta API error {response.status_code}: {response.text}")
                data = response.json()
                templates.extend(data.get("data") or [])
                url = (data.get("paging") or {}).get("next")
                params = None  # the 'next' URL already carries every query param

        return templates

    async def create_template(
        self, name: str, category: str, language: str, components: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Submit a new template to Meta for review (WhatsApp Template
        Management Phase 3 — "Submit to Meta"). Raises RuntimeError with
        Meta's real response body on any non-2xx (malformed template,
        duplicate name, invalid component, etc.) — the caller
        (WhatsAppTemplateService.submit_to_meta) surfaces this verbatim and
        must NOT set status to PENDING when this raises; only a successful
        return here represents genuine Meta acceptance (still PENDING
        review, never APPROVED — approval is only ever learned via
        list_templates()/sync, never assumed here).
        """
        if not self.business_account_id:
            raise RuntimeError("MetaProvider not configured (missing business_account_id)")

        url = f"{self.GRAPH_BASE_URL}/{self.api_version}/{self.business_account_id}/message_templates"
        body = {"name": name, "category": category, "language": language, "components": components}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self._headers(), json=body)

        if response.status_code >= 400:
            raise RuntimeError(f"Meta API error {response.status_code}: {response.text}")

        return response.json()

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
