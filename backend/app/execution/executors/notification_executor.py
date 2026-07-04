"""Notification node executor.

Sends an internal alert to workspace operators. For Sprint 2 this is a
dummy execution that only creates an execution log and returns success.
"""

import logging
from datetime import datetime
from typing import Any, Dict

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
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_data = node.get("data") or {}
        node_id = node.get("id", "notification")

        channel = node_data.get("channel", "in-app")
        message = node_data.get("message", "")

        logger.info(
            "NotificationExecutor: dummy notification for lead=%s node=%s channel=%s",
            lead_id, node_id, channel,
        )

        output_data = {
            "message": message or "Operator notification simulated",
            "channel": channel,
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"notification_config": node_data},
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
