"""Change Lead Stage node executor.

Changes a lead's stage in the CRM.  Delegates to
:class:`CRMIntegration <app.integrations.CRMIntegration>`.

Configuration (node.config):
    target_stage (str): Target stage key (supports ``{{variable}}``).
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.integrations import IntegrationFactory
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class ChangeLeadStageExecutor(BaseNodeExecutor):

    @property
    def node_type(self) -> str:
        return "change_lead_stage"

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
        node_id = node.get("id", "change_lead_stage")

        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None
        raw_target_stage = node_config.get("target_stage", "")

        resolved_target_stage = renderer.render(raw_target_stage) if renderer else raw_target_stage

        logger.info(
            "ChangeLeadStageExecutor: lead=%s node=%s target_stage=%s",
            lead_id, node_id, resolved_target_stage,
        )

        request_payload = {
            "action": "change_stage",
            "lead_id": lead_id,
            "target_stage": resolved_target_stage,
        }
        integration = IntegrationFactory.get("crm")
        integration_response = await integration.execute(request_payload)

        output_data = {
            "message": f"Lead stage changed to '{resolved_target_stage}'",
            "resolved_target_stage": resolved_target_stage,
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
                input_data={"target_stage": raw_target_stage},
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
