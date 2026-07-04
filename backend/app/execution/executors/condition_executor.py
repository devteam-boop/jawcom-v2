"""Condition node executor.

For Sprint 2 the condition evaluator always returns TRUE. In future sprints
this will support lead data, CRM data and AI-generated conditions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class ConditionExecutor(BaseNodeExecutor):
    """Executor for flow condition nodes."""

    @property
    def node_type(self) -> str:
        return "condition"

    async def execute(
        self,
        node: Dict[str, Any],
        running_instance: Any,
        lead_id: int,
        context: Dict[str, Any],
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_data = node.get("data") or {}
        node_id = node.get("id", "condition")

        # Sprint 2: dummy evaluator always returns True.
        # Later this will parse node_data["field"], ["operator"], ["value"].
        condition_result = True
        logger.info(
            "ConditionExecutor: evaluating condition for lead=%s node=%s -> %s",
            lead_id, node_id, condition_result,
        )

        next_node_id: Optional[str] = None
        if condition_result:
            next_node_id = node_data.get("true_next_node_id")
        else:
            next_node_id = node_data.get("false_next_node_id")

        output_data = {
            "condition_result": condition_result,
            "message": "Condition evaluated to TRUE (Sprint 2 dummy)",
        }

        output = {
            "next_node_id": next_node_id,
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"condition": node_data},
                output_data=output_data,
                started_at=started_at,
            ),
            **output_data,
        }

        return ExecutionResult(
            success=True,
            next_node_id=next_node_id,
            updated_context=context,
            status="success",
            output=output,
        )
