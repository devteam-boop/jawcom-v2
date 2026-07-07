"""Notification node executor.

Resolves ``{{variable}}`` placeholders in title and message,
builds a request payload, and delegates dispatching to
:class:`NotificationIntegration <app.integrations.NotificationIntegration>`.

Configuration (node.config):
    title (str): Notification title (supports ``{{variable}}``).
    message (str): Notification body message (supports ``{{variable}}``).
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.integrations import IntegrationFactory
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class NotificationExecutor(BaseNodeExecutor):
    """Executor for flow notification nodes."""

    @property
    def node_type(self) -> str:
        return "notification"

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
        node_id = node.get("id", "notification")

        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None
        raw_title = node_config.get("title", "")
        raw_message = node_config.get("message", "")

        resolved_title = renderer.render(raw_title) if renderer else raw_title
        resolved_message = renderer.render(raw_message) if renderer else raw_message

        logger.info(
            "NotificationExecutor: resolved notification for lead=%s node=%s title=%s",
            lead_id, node_id, resolved_title,
        )

        # ── Build integration request ──────────────────────────────
        request_payload = {
            "title": resolved_title,
            "message": resolved_message,
        }
        integration = IntegrationFactory.get("notification")
        integration_response = await integration.execute(request_payload)

        output_data = {
            "message": resolved_message or "Operator notification simulated",
            "resolved_title": resolved_title,
            "resolved_message": resolved_message,
            "raw_title": raw_title,
            "raw_message": raw_message,
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
                input_data={"notification_config": node_config},
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
