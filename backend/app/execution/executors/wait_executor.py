"""Wait node executor.

Wait nodes pause the journey until a specific time or an external event.
The executor calculates how long to wait, stores ``resume_at`` in the
updated context with ``_wait: True``, and returns ``status="skipped"``
so the engine pauses traversal and transitions the instance to ``waiting``.

Configuration (node.config):
    duration (int): The duration to wait.
    unit (str): Unit of duration (minutes, hours, days, weeks).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)

UNIT_SECONDS: Dict[str, int] = {
    "minutes": 60,
    "hours": 3600,
    "days": 86400,
    "weeks": 604800,
}


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
        exec_ctx: Any = None,
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_config = node.get("config") or {}
        node_id = node.get("id", "wait")

        duration = node_config.get("duration", 0)
        unit = node_config.get("unit", "days")

        total_seconds = duration * UNIT_SECONDS.get(unit, 86400)
        resume_at = datetime.utcnow() + timedelta(seconds=total_seconds)
        resume_at_iso = resume_at.isoformat()

        logger.info(
            "WaitExecutor: waiting %s %s until %s for lead=%s node=%s",
            duration, unit, resume_at_iso, lead_id, node_id,
        )

        output_data = {
            "duration": duration,
            "unit": unit,
            "resume_at": resume_at_iso,
            "message": f"Waiting {duration} {unit} until {resume_at_iso}",
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"wait_config": node_config},
                output_data=output_data,
                started_at=started_at,
            ),
            **output_data,
        }

        return ExecutionResult(
            success=True,
            updated_context={"resume_at": resume_at_iso, "_wait": True},
            status="skipped",
            output=output,
        )
