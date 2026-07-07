"""Notification integration — simulated.

Logs the outgoing payload.  No real push / in-app notification
infrastructure is called.
"""

import logging
from typing import Any, Dict
from uuid import uuid4

from .base import BaseIntegration

logger = logging.getLogger(__name__)


class NotificationIntegration(BaseIntegration):
    """Simulated Notification adapter — logs payload, returns success."""

    @property
    def name(self) -> str:
        return "notification"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(
            "NotificationIntegration.execute title=%s message=%s",
            payload.get("title"),
            payload.get("message"),
        )
        return {
            "success": True,
            "provider": "notification",
            "notification_id": str(uuid4()),
            "simulated": True,
        }
