"""Update Company node executor.

Updates a company field in the CRM.  Delegates to
:class:`CRMIntegration <app.integrations.CRMIntegration>`.

Configuration (node.config):
    company_field (str): The company field to update (e.g. ``name``, ``industry``).
    value (str): New value (supports ``{{variable}}``).
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.integrations import IntegrationFactory
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class UpdateCompanyExecutor(BaseNodeExecutor):

    @property
    def node_type(self) -> str:
        return "update_company"

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
        node_id = node.get("id", "update_company")

        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None
        company_field = node_config.get("company_field", "")
        raw_value = node_config.get("value", "")

        resolved_field = renderer.render(company_field) if renderer else company_field
        resolved_value = renderer.render(raw_value) if renderer else raw_value

        logger.info(
            "UpdateCompanyExecutor: lead=%s node=%s field=%s value=%s",
            lead_id, node_id, resolved_field, resolved_value,
        )

        request_payload = {
            "action": "update_company",
            "lead_id": lead_id,
            "field": resolved_field,
            "value": resolved_value,
        }
        integration = IntegrationFactory.get("crm")
        integration_response = await integration.execute(request_payload)

        output_data = {
            "message": f"Company field '{resolved_field}' updated to '{resolved_value}'",
            "resolved_field": resolved_field,
            "resolved_value": resolved_value,
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
                input_data={"company_field": company_field, "value": raw_value},
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
