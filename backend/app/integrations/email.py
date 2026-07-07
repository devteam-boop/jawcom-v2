"""Email integration — simulated for Sprint 11.

Logs the outgoing payload so the execution monitor shows what *would*
be sent.  No real SMTP is called.
"""

import logging
from typing import Any, Dict
from uuid import uuid4

from .base import BaseIntegration
from .config import IntegrationConfig

logger = logging.getLogger(__name__)


class EmailIntegration(BaseIntegration):
    """Simulated Email adapter — logs payload, returns success.

    Registered as ``"email_dummy"`` (see ``app/integrations/__init__.py``);
    ``"email"`` now resolves to ``JawisEmailIntegration`` by default.
    """

    @property
    def name(self) -> str:
        return "email_dummy"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(
            "EmailIntegration.execute subject=%s template=%s recipient=%s",
            payload.get("subject"),
            payload.get("template_name"),
            payload.get("recipient"),
        )
        return {
            "success": True,
            "provider": "email",
            "message_id": str(uuid4()),
            "simulated": True,
        }

    async def health(self) -> Dict[str, Any]:
        cfg = IntegrationConfig()
        configured = bool(cfg.email_api_key and cfg.email_sender)
        return {
            "status": "healthy" if configured else "unconfigured",
            "name": self.name,
            "configured": configured,
        }
