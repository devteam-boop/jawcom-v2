"""End node executor.

Marks the running instance as completed and terminates traversal.
The engine treats the absence of a next_node as the end of the branch.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class EndExecutor(BaseNodeExecutor):
    """Executor for flow end nodes."""

    @property
    def node_type(self) -> str:
        return "end"

    async def execute(
        self,
        node: Dict[str, Any],
        running_instance: Any,
        lead_id: int,
        context: Dict[str, Any],
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_id = node.get("id", "end")

        logger.info(
            "EndExecutor: journey completed for lead=%s node=%s",
            lead_id, node_id,
        )

        output_data = {
            "message": "Journey completed",
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={},
                output_data=output_data,
                started_at=started_at,
            ),
            **output_data,
        }

        return ExecutionResult(
            success=True,
            next_node_id=None,
            updated_context=context,
            status="success",
            output=output,
        )
