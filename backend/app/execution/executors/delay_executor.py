"""Delay node executor — Time Scheduler.

Delay nodes pause internal execution for a computed duration. Unlike Wait
nodes, they do NOT transition the instance to ``waiting`` status — the
instance stays ``running`` with a ``resume_at`` timestamp stored in its
data. The scheduler (SchedulerService.find_due_delays) resumes traversal
when the delay expires.

Configuration (node.config):
    mode (str, optional): "fixed" (default — backward compatible with every
        existing saved Delay node, which has no "mode" key at all) or
        "relative_to_lead_date".

    Fixed mode:
        duration (int): The delay duration.
        unit (str): Unit of duration (minutes, hours, days, weeks).

    Relative-to-lead-date mode:
        lead_date_field (str): Lead field to schedule relative to, e.g.
            "tour_datetime", "move_in_date", "proposal_expiry".
        offset_value (int): Signed offset (negative = before the lead date,
            e.g. -24 for "24 hours before the tour").
        offset_unit (str): Unit of offset_value (minutes, hours, days, weeks).
        If the configured lead_date_field is empty/missing, the node FAILS
        (does not silently skip) — see the missing-field branch below.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from app.config.settings import get_settings

from .base import BaseNodeExecutor, ExecutionResult
from .scheduling_utils import UNIT_SECONDS, apply_offset, resolve_lead_datetime_field
from .utils import build_log_payload, record_audit_failure

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
        exec_ctx: Any = None,
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_config = node.get("config") or {}
        node_id = node.get("id", "delay")

        mode = node_config.get("mode", "fixed")

        if mode == "relative_to_lead_date":
            return await self._execute_relative_to_lead_date(
                node_config, running_instance, lead_id, context, exec_ctx, node_id, started_at,
            )

        # ── Fixed mode (default) — identical to the original implementation ──
        duration = node_config.get("duration", 0)
        unit = node_config.get("unit", "minutes")

        total_seconds = duration * UNIT_SECONDS.get(unit, 60)
        resume_at = datetime.utcnow() + timedelta(seconds=total_seconds)
        resume_at_iso = resume_at.isoformat()

        logger.info(
            "DelayExecutor: delaying %s %s until %s for lead=%s node=%s",
            duration, unit, resume_at_iso, lead_id, node_id,
        )
        logger.info(
            "Delay scheduled: lead_id=%s node_id=%s resume_at=%s mode=%s",
            lead_id, node_id, resume_at_iso, mode,
        )

        output_data = {
            "mode": mode,
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

    async def _execute_relative_to_lead_date(
        self, node_config, running_instance, lead_id, context, exec_ctx, node_id, started_at,
    ) -> ExecutionResult:
        lead_date_field = node_config.get("lead_date_field", "")
        offset_value = node_config.get("offset_value", 0)
        offset_unit = node_config.get("offset_unit", "hours")

        lead = (getattr(exec_ctx, "lead", None) if exec_ctx else None) or {}
        settings = get_settings()
        lead_date = resolve_lead_datetime_field(
            lead, lead_date_field, default_tz=settings.JAWIS_LEAD_DATE_TIMEZONE,
        )

        if lead_date is None:
            error_message = (
                f"Delay node: lead.{lead_date_field or '<unset>'} is empty — "
                f"cannot schedule relative to a missing date"
            )
            logger.error(
                "DelayExecutor: %s — lead=%s node=%s",
                error_message, lead_id, node_id,
            )
            await record_audit_failure(
                getattr(exec_ctx, "session", None) if exec_ctx else None,
                lead_id=lead_id,
                node_id=node_id,
                running_instance_id=str(running_instance.id),
                journey_id=getattr(running_instance, "journey_id", None),
                payload={
                    "reason": "missing_lead_date_field",
                    "lead_date_field": lead_date_field,
                    "timestamp": started_at.isoformat(),
                },
            )
            output_data = {
                "mode": "relative_to_lead_date",
                "lead_date_field": lead_date_field,
                "message": error_message,
                "status": "failed_missing_lead_date",
            }
            output = {
                "log_payload": build_log_payload(
                    flow_definition_id=context.get("flow_definition_id", ""),
                    running_instance_id=str(running_instance.id),
                    lead_id=lead_id,
                    node_id=node_id,
                    node_type=self.node_type,
                    status="failed",
                    input_data={"delay_config": node_config},
                    output_data=output_data,
                    error_message=error_message,
                    started_at=started_at,
                ),
                **output_data,
            }
            return ExecutionResult(
                success=False,
                status="failed",
                error=error_message,
                output=output,
            )

        resume_at = apply_offset(lead_date, offset_value, offset_unit)
        resume_at_iso = resume_at.isoformat()

        logger.info(
            "DelayExecutor: relative delay for lead=%s node=%s lead_date_field=%s "
            "lead_date=%s offset=%s %s -> resume_at=%s",
            lead_id, node_id, lead_date_field, lead_date.isoformat(),
            offset_value, offset_unit, resume_at_iso,
        )
        logger.info(
            "Delay scheduled: lead_id=%s node_id=%s resume_at=%s mode=relative_to_lead_date",
            lead_id, node_id, resume_at_iso,
        )

        output_data = {
            "mode": "relative_to_lead_date",
            "lead_date_field": lead_date_field,
            "lead_date": lead_date.isoformat(),
            "offset_value": offset_value,
            "offset_unit": offset_unit,
            "resume_at": resume_at_iso,
            "message": f"Delaying until {resume_at_iso} ({offset_value} {offset_unit} relative to {lead_date_field})",
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
