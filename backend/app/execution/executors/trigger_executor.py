"""Trigger node executor.

The trigger node is the entry point of a journey. It is logged once when
a running instance is created; the engine still dispatches it through the
executor framework for consistency.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class TriggerExecutor(BaseNodeExecutor):
    """Executor for flow trigger nodes."""

    @property
    def node_type(self) -> str:
        return "trigger"

    async def execute(
        self,
        node: Dict[str, Any],
        running_instance: Any,
        lead_id: int,
        context: Dict[str, Any],
        exec_ctx: Any = None,
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        stage_key = context.get("trigger_stage_key", "unknown")
        logger.info(
            "TriggerExecutor: journey triggered for lead=%s stage=%s",
            lead_id, stage_key,
        )

        output = {
            "message": "Journey triggered",
            "stage_key": stage_key,
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node.get("id", "trigger"),
                node_type=self.node_type,
                status="success",
                input_data={"event": "trigger"},
                output_data={"trigger_stage_key": stage_key},
                started_at=started_at,
            ),
        }

        return ExecutionResult(
            success=True,
            updated_context=context,
            status="success",
            output=output,
        )
