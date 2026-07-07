"""Create CRM Task node executor.

Creates a task in the CRM.  Delegates to
:class:`CRMIntegration <app.integrations.CRMIntegration>`.

Configuration (node.config):
    title (str): Task title (supports ``{{variable}}``).
    description (str): Task description (supports ``{{variable}}``).
    due_date (str): Due date (supports ``{{variable}}``).
    priority (str): Priority level (low, medium, high).
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.integrations import IntegrationFactory
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class CreateCRMTaskExecutor(BaseNodeExecutor):

    @property
    def node_type(self) -> str:
        return "create_crm_task"

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
        node_id = node.get("id", "create_crm_task")

        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None
        raw_title = node_config.get("title", "")
        raw_description = node_config.get("description", "")
        raw_due_date = node_config.get("due_date", "")
        raw_priority = node_config.get("priority", "medium")

        resolved_title = renderer.render(raw_title) if renderer else raw_title
        resolved_description = renderer.render(raw_description) if renderer else raw_description
        resolved_due_date = renderer.render(raw_due_date) if renderer else raw_due_date
        resolved_priority = renderer.render(raw_priority) if renderer else raw_priority

        logger.info(
            "CreateCRMTaskExecutor: lead=%s node=%s title=%s",
            lead_id, node_id, resolved_title,
        )

        request_payload = {
            "action": "create_task",
            "lead_id": lead_id,
            "title": resolved_title,
            "description": resolved_description,
            "due_date": resolved_due_date,
            "priority": resolved_priority,
        }
        integration = IntegrationFactory.get("crm")
        integration_response = await integration.execute(request_payload)

        output_data = {
            "message": f"Task '{resolved_title}' created",
            "resolved_title": resolved_title,
            "resolved_description": resolved_description,
            "resolved_due_date": resolved_due_date,
            "resolved_priority": resolved_priority,
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
                input_data={
                    "title": raw_title,
                    "description": raw_description,
                    "due_date": raw_due_date,
                    "priority": raw_priority,
                },
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
