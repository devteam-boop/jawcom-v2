"""Create Note node executor.

Creates a note on a lead in the CRM.  Delegates to
:class:`CRMIntegration <app.integrations.CRMIntegration>`.

Configuration (node.config):
    note (str): Note content (supports ``{{variable}}``).
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.integrations import IntegrationFactory
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class CreateNoteExecutor(BaseNodeExecutor):

    @property
    def node_type(self) -> str:
        return "create_note"

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
        node_id = node.get("id", "create_note")

        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None
        raw_note = node_config.get("note", "")

        resolved_note = renderer.render(raw_note) if renderer else raw_note

        logger.info(
            "CreateNoteExecutor: lead=%s node=%s",
            lead_id, node_id,
        )

        request_payload = {
            "action": "create_note",
            "lead_id": lead_id,
            "note": resolved_note,
        }
        integration = IntegrationFactory.get("crm")
        integration_response = await integration.execute(request_payload)

        output_data = {
            "message": f"Note created for lead {lead_id}",
            "resolved_note": resolved_note,
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
                input_data={"note": raw_note},
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
