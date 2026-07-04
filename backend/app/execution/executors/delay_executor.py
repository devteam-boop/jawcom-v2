"""Delay node executor.

For Sprint 2 the delay is also skipped in test mode: we log the configured
duration and return success without blocking the traversal.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class DelayExecutor(BaseNodeExecutor):
    """Executor for flow delay nodes."""

    @property
    def node_type(self) -> str:
        return "delay"

    async def execute(
        self,
        node: Dict[str, Any],
        running_instance: Any,
        lead_id: int,
        context: Dict[str, Any],
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_data = node.get("data") or {}
        node_id = node.get("id", "delay")

        duration = node_data.get("duration", 0)
        unit = node_data.get("unit", "minutes")

        logger.info(
            "DelayExecutor: delay of %s %s skipped in test mode for lead=%s node=%s",
            duration, unit, lead_id, node_id,
        )

        output_data = {
            "duration": duration,
            "unit": unit,
            "message": "Delay skipped in test mode",
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"delay_config": node_data},
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
