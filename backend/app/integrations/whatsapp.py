"""WhatsApp integration — simulated for Sprint 10.

Logs the outgoing payload so the execution monitor shows what *would*
be sent.  No real Meta Cloud API is called.
"""

import logging
from typing import Any, Dict
from uuid import uuid4

from .base import BaseIntegration
from .config import IntegrationConfig

logger = logging.getLogger(__name__)


class WhatsAppIntegration(BaseIntegration):
    """Simulated WhatsApp adapter — logs payload, returns success.

    Registered as ``"whatsapp_dummy"`` (see ``app/integrations/__init__.py``);
    ``"whatsapp"`` now resolves to ``JawisWhatsAppIntegration`` by default.
    """

    @property
    def name(self) -> str:
        return "whatsapp_dummy"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(
            "WhatsAppIntegration.execute template=%s recipient=%s variables=%s",
            payload.get("template_name"),
            payload.get("recipient"),
            payload.get("variables"),
        )
        return {
            "success": True,
            "provider": "whatsapp",
            "message_id": str(uuid4()),
            "simulated": True,
        }

    async def health(self) -> Dict[str, Any]:
        cfg = IntegrationConfig()
        configured = bool(cfg.whatsapp_api_key and cfg.whatsapp_phone_number_id)
        return {
            "status": "healthy" if configured else "unconfigured",
            "name": self.name,
            "configured": configured,
        }
