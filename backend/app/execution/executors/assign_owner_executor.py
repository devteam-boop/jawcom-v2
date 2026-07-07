"""Assign Owner node executor.

Assigns a lead to an owner in the CRM.  Delegates to
:class:`CRMIntegration <app.integrations.CRMIntegration>`.

Configuration (node.config):
    owner_id (str): Owner identifier (supports ``{{variable}}``).
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.integrations import IntegrationFactory
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class AssignOwnerExecutor(BaseNodeExecutor):

    @property
    def node_type(self) -> str:
        return "assign_owner"

    async def execute(
        self,
        node: Dict[str, Any],
        running_instance: Any,
        lead_id: int,
        context: Dict[str, Any],
        exec_ctx: Any = None,
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_config = node.get("config") or {}
        node_id = node.get("id", "assign_owner")

        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None
        raw_owner_id = node_config.get("owner_id", "")

        resolved_owner_id = renderer.render(raw_owner_id) if renderer else raw_owner_id

        logger.info(
            "AssignOwnerExecutor: lead=%s node=%s owner=%s",
            lead_id, node_id, resolved_owner_id,
        )

        request_payload = {
            "action": "assign_owner",
            "lead_id": lead_id,
            "owner_id": resolved_owner_id,
        }
        integration = IntegrationFactory.get("crm")
        integration_response = await integration.execute(request_payload)

        output_data = {
            "message": f"Lead assigned to owner '{resolved_owner_id}'",
            "resolved_owner_id": resolved_owner_id,
            "provider_response": integration_response,
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"owner_id": raw_owner_id},
                output_data=output_data,
                started_at=started_at,
            ),
            **output_data,
        }

        return ExecutionResult(
            success=True,
            updated_context=context,
            status="success",
            output=output,
        )
