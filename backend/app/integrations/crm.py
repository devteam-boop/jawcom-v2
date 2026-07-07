"""CRM integration — dummy and JAWIS backends.

Two implementations of the same ``BaseIntegration`` interface:

1. ``DummyCRMIntegration`` — logs payload, returns simulated success (the
   original Sprint 12+13 behaviour).

2. ``JawisCRMIntegration`` — calls the real JAWIS CRM API for each action.

The factory uses ``JAWIS_CRM_PROVIDER`` env var to decide which one to
return when ``IntegrationFactory.get("crm")`` is called.
"""

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from .base import BaseIntegration

logger = logging.getLogger(__name__)


class DummyCRMIntegration(BaseIntegration):
    """Simulated CRM adapter — logs payload, returns success."""

    @property
    def name(self) -> str:
        return "crm_dummy"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "unknown")
        logger.info(
            "DummyCRMIntegration.execute action=%s payload=%s",
            action, {k: v for k, v in payload.items() if k != "action"},
        )
        return {
            "success": True,
            "provider": "crm",
            "action": action,
            "operation_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "simulated": True,
        }
