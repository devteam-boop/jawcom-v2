"""JAWIS CRM integration — calls the real JAWIS CRM API.

Replaces ``DummyCRMIntegration`` when ``JAWIS_CRM_PROVIDER=jawis``.

Supported actions match the 6 CRM executors:
  - update_lead
  - update_company
  - assign_owner
  - change_stage
  - create_task
  - create_note
"""

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from app.jawis.client import get_jawis_client

from .base import BaseIntegration

logger = logging.getLogger(__name__)


class JawisCRMIntegration(BaseIntegration):
    """Real CRM adapter — delegates to the JAWIS CRM API."""

    @property
    def name(self) -> str:
        return "crm_jawis"

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "unknown")
        client = get_jawis_client()

        logger.info(
            "JawisCRMIntegration.execute action=%s payload=%s",
            action, {k: v for k, v in payload.items() if k != "action"},
        )

        try:
            result = await self._route_action(client, action, payload)
            return {
                "success": True,
                "provider": "crm",
                "action": action,
                "operation_id": result.get("id", str(uuid4())),
                "timestamp": datetime.utcnow().isoformat(),
                "data": result,
            }
        except Exception as exc:
            logger.exception("JawisCRMIntegration failed for action=%s: %s", action, exc)
            return {
                "success": False,
                "provider": "crm",
                "action": action,
                "error": str(exc),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _route_action(self, client: Any, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to the correct JAWIS API call based on *action*."""
        from app.jawis.client import JawisApiError

        lead_id = payload.get("lead_id", "")

        if action == "update_lead":
            field = payload.get("field", "")
            value = payload.get("value", "")
            return await client._make_request(
                f"/api/leads/{lead_id}",
                params={"method": "PATCH", field: value},
            )

        elif action == "update_company":
            company_id = payload.get("company_id", "")
            field = payload.get("field", "")
            value = payload.get("value", "")
            return await client._make_request(
                f"/api/companies/{company_id}",
                params={"method": "PATCH", field: value},
            )

        elif action == "assign_owner":
            owner_id = payload.get("owner_id", "")
            return await client._make_request(
                f"/api/leads/{lead_id}/assign",
                params={"user_id": owner_id},
            )

        elif action == "change_stage":
            target_stage = payload.get("target_stage", "")
            return await client._make_request(
                f"/api/leads/{lead_id}/stage",
                params={"stage_key": target_stage},
            )

        elif action == "create_task":
            return await client._make_request(
                f"/api/leads/{lead_id}/tasks",
                params={
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "due_date": payload.get("due_date", ""),
                },
            )

        elif action == "create_note":
            return await client._make_request(
                f"/api/leads/{lead_id}/notes",
                params={"content": payload.get("note", "")},
            )

        else:
            raise ValueError(f"Unknown CRM action: {action}")
