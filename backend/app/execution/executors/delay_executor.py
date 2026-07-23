"""Delay node executor.

Delay nodes pause internal execution for a set duration. Unlike Wait nodes,
they do NOT transition the instance to ``waiting`` status — the instance
stays ``running`` with a ``resume_at`` timestamp stored in its data.
The scheduler silently resumes traversal when the delay expires.

Configuration (node.config):
    duration (int): The delay duration.
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
        exec_ctx: Any = None,
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_config = node.get("config") or {}
        node_id = node.get("id", "delay")

        duration = node_config.get("duration", 0)
        unit = node_config.get("unit", "minutes")

        total_seconds = duration * UNIT_SECONDS.get(unit, 60)
        resume_at = datetime.utcnow() + timedelta(seconds=total_seconds)
        resume_at_iso = resume_at.isoformat()

        logger.info(
            "DelayExecutor: delaying %s %s until %s for lead=%s node=%s",
            duration, unit, resume_at_iso, lead_id, node_id,
        )
        # TEMPORARY DIAGNOSTIC LOG — Delay node resume investigation.
        logger.info(
            "Delay scheduled: lead_id=%s node_id=%s resume_at=%s",
            lead_id, node_id, resume_at_iso,
        )

        output_data = {
            "duration": duration,
            "unit": unit,
            "resume_at": resume_at_iso,
            "message": f"Delaying {duration} {unit} until {resume_at_iso}",
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"delay_config": node_config},
                output_data=output_data,
                started_at=started_at,
            ),
            **output_data,
        }

        return ExecutionResult(
            success=True,
            updated_context={"resume_at": resume_at_iso},
            status="skipped",
            output=output,
        )
