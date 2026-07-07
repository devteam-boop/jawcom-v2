"""JAWIS Communication integration — real WhatsApp/Email sending via the
JAWIS Sprint-1 messaging APIs.

Replaces the simulated ``WhatsAppIntegration``/``EmailIntegration`` as the
default backend for the ``"whatsapp"``/``"email"`` integration names.

Error-handling is deliberately different from ``JawisCRMIntegration``: that
integration catches failures and returns a ``{"success": False, ...}`` dict,
which every executor today ignores (they always build
``ExecutionResult(success=True, ...)`` regardless of the integration's
returned payload). To make "JAWIS unavailable" actually surface as a failed
node/instance — without changing any executor or the engine — this
integration instead *raises* on failure. The uncaught exception propagates
out of ``executor.execute()`` into the engine's existing
``_execute_node()`` exception handler, which already creates a failed log
and calls ``instance_service.fail()`` with no retry. This is the same,
already-existing mechanism used for any other executor error.
"""

import logging
from typing import Any, Dict

import httpx

from .base import BaseIntegration
from .config import IntegrationConfig

logger = logging.getLogger(__name__)


class JawisCommunicationError(Exception):
    """Raised when the JAWIS Communication API is unavailable or returns an error."""

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class JawisCommunicationIntegration(BaseIntegration):
    """Shared base for JAWIS Sprint-1 messaging endpoints.

    Subclasses declare only ``name`` and ``_endpoint``; request building,
    response handling, and error handling are implemented exactly once here.
    """

    _endpoint: str = ""

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cfg = IntegrationConfig()
        if not cfg.jawis_base_url or not cfg.jawis_api_token:
            raise JawisCommunicationError(
                f"JAWIS Communication API not configured "
                f"(JAWIS_BASE_URL/JAWIS_API_TOKEN missing) — {self.name} send aborted"
            )

        headers = {"Authorization": f"Bearer {cfg.jawis_api_token}"}

        try:
            async with httpx.AsyncClient(
                base_url=cfg.jawis_base_url, headers=headers, timeout=30.0
            ) as client:
                response = await client.post(self._endpoint, json=payload)
        except httpx.RequestError as exc:
            logger.error("%s: JAWIS Communication API unavailable — %s", self.name, exc)
            raise JawisCommunicationError(
                f"JAWIS Communication API unavailable: {exc}"
            ) from exc

        if response.status_code >= 400:
            logger.error(
                "%s: JAWIS Communication API returned %s — %s",
                self.name, response.status_code, response.text,
            )
            raise JawisCommunicationError(
                f"JAWIS Communication API error {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        logger.info(
            "%s: JAWIS Communication API responded status=%s message_id=%s",
            self.name, data.get("status"), data.get("message_id"),
        )
        # Returned exactly as received — executors store this verbatim as
        # `provider_response`, no transformation or key renaming.
        return data

    async def health(self) -> Dict[str, Any]:
        cfg = IntegrationConfig()
        configured = bool(cfg.jawis_base_url and cfg.jawis_api_token)
        return {
            "status": "healthy" if configured else "unconfigured",
            "name": self.name,
            "configured": configured,
        }


class JawisWhatsAppIntegration(JawisCommunicationIntegration):
    """Sends WhatsApp messages via ``POST /api/messages/whatsapp/send``."""

    _endpoint = "/api/messages/whatsapp/send"

    @property
    def name(self) -> str:
        return "whatsapp"


class JawisEmailIntegration(JawisCommunicationIntegration):
    """Sends email via ``POST /api/messages/email/send``."""

    _endpoint = "/api/messages/email/send"

    @property
    def name(self) -> str:
        return "email"
