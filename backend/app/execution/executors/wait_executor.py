"""Wait node executor.

Wait nodes pause the journey until a specific time or an external event.
For Sprint 2 scheduling is intentionally NOT implemented; traversal resumes
immediately and logs that waiting was skipped in test mode.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class WaitExecutor(BaseNodeExecutor):
    """Executor for flow wait nodes."""

    @property
    def node_type(self) -> str:
        return "wait"

    async def execute(
        self,
        node: Dict[str, Any],
        running_instance: Any,
        lead_id: int,
        context: Dict[str, Any],
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_id = node.get("id", "wait")

        logger.info(
            "WaitExecutor: waiting skipped in test mode for lead=%s node=%s",
            lead_id, node_id,
        )

        output_data = {
            "message": "Waiting skipped in test mode",
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"wait_config": node.get("data") or {}},
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
