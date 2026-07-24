"""Wait node executor — Event Scheduler.

Wait pauses the journey until something happens — a fixed duration/specific
datetime elapsing, an external event occurring, or a manual approval — NOT
merely a duration like Delay. All wait_types converge on the same generic
resume primitive (ExecutionEngine.resume_instance), differing only in what
condition is stored in instance.data while paused and what causes the
scheduler/an external caller to resume it.

Configuration (node.config):
    wait_type (str, optional): "duration" (default — backward compatible
        with every existing saved Wait node, which has no "wait_type" key at
        all), "specific_datetime", "replied", "stage_changed",
        "field_condition", "manual_approval", or "webhook_event".

    wait_type == "duration" (default):
        duration (int), unit (str: minutes/hours/days/weeks).

    wait_type == "specific_datetime":
        target_datetime (str, optional): literal absolute ISO datetime.
        target_lead_field (str, optional): a lead field to read the target
            datetime from instead (e.g. "tour_datetime"). One of the two
            must be set; if neither resolves, the node fails.

    wait_type == "replied":
        channel (str, optional, default "whatsapp").
        timeout (int, optional): duration after which, absent a reply, this
            node is considered timed out. unit (str, optional, default
            "minutes"). Omit both (every pre-existing "replied" Wait node)
            to wait for a reply indefinitely — unchanged behavior.
        replied_next_node_id / timeout_next_node_id (str, optional): the two
            single next-node targets ExecutionEngine._resume_from routes to
            on resume — the reply branch or the timeout branch, never both.
            Required together when "timeout" is set (see
            flow_validation_service.py); a plain single-successor "replied"
            Wait (no timeout) ignores both and keeps following its one
            outgoing edge as before.

    wait_type in {"stage_changed", "field_condition"}:
        field (str): lead field to watch, e.g. "stage" or "visit_completed".
        operator (str): same vocabulary as Condition nodes (equals,
            not_equals, greater_than, less_than, contains, starts_with,
            ends_with).
        value (str): value to compare against.

    wait_type == "manual_approval":
        title, description, approver, approval_type, timeout — identical
        shape to the standalone Approval node (this delegates to the exact
        same pause contract, not a new mechanism).

    wait_type == "webhook_event":
        event_key (str): arbitrary caller-defined key an external system
            posts to POST /api/journeys/instances/{instance_id}/trigger-event
            to resume this node.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import uuid4

from app.config.settings import get_settings

from .base import BaseNodeExecutor, ExecutionResult
from .scheduling_utils import UNIT_SECONDS, parse_datetime_value, resolve_lead_datetime_field
from .utils import build_log_payload

logger = logging.getLogger(__name__)

# wait_types that pause on an external condition rather than a clock time —
# no resume_at at all; resumed via wait_condition_service.py / the scheduler's
# find_due_events(), or (webhook_event) via the dedicated trigger-event route.
_EVENT_WAIT_TYPES = {"replied", "stage_changed", "field_condition", "webhook_event"}


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

        wait_type = node_config.get("wait_type", "duration")

        if wait_type == "specific_datetime":
            return self._execute_specific_datetime(node_config, running_instance, lead_id, context, exec_ctx, node_id, started_at)
        if wait_type == "manual_approval":
            return self._execute_manual_approval(node, node_config, exec_ctx, node_id)
        if wait_type in _EVENT_WAIT_TYPES:
            return self._execute_event_wait(wait_type, node_config, running_instance, lead_id, context, node_id, started_at)

        # ── "duration" (default) — identical to the original implementation ──
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
            "wait_type": "duration",
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

    def _execute_specific_datetime(
        self, node_config, running_instance, lead_id, context, exec_ctx, node_id, started_at,
    ) -> ExecutionResult:
        target_datetime_literal = node_config.get("target_datetime")
        target_lead_field = node_config.get("target_lead_field")
        settings = get_settings()
        lead = (getattr(exec_ctx, "lead", None) if exec_ctx else None) or {}

        resume_at = None
        if target_lead_field:
            resume_at = resolve_lead_datetime_field(
                lead, target_lead_field, default_tz=settings.JAWIS_LEAD_DATE_TIMEZONE,
            )
        elif target_datetime_literal:
            resume_at = parse_datetime_value(
                target_datetime_literal, default_tz=settings.JAWIS_LEAD_DATE_TIMEZONE,
                _log_context="target_datetime",
            )

        if resume_at is None:
            error_message = (
                f"Wait node: could not resolve a target datetime "
                f"(target_lead_field={target_lead_field!r}, target_datetime={target_datetime_literal!r})"
            )
            logger.error("WaitExecutor: %s — lead=%s node=%s", error_message, lead_id, node_id)
            return ExecutionResult(success=False, status="failed", error=error_message)

        resume_at_iso = resume_at.isoformat()
        logger.info(
            "WaitExecutor: specific_datetime wait for lead=%s node=%s resume_at=%s",
            lead_id, node_id, resume_at_iso,
        )

        output_data = {
            "wait_type": "specific_datetime",
            "resume_at": resume_at_iso,
            "message": f"Waiting until {resume_at_iso}",
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

    def _execute_manual_approval(self, node, node_config, exec_ctx, node_id) -> ExecutionResult:
        """Delegates to the exact same pause contract as the standalone
        ApprovalExecutor (execution/executors/approval_executor.py) — no new
        mechanism, just an alternate entry point so the redesigned Wait node
        can offer "wait until manual approval" without duplicating the
        approval infrastructure."""
        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None

        approval_id = str(uuid4())
        title = renderer.render(node_config.get("title", "")) if renderer else node_config.get("title", "")
        description = renderer.render(node_config.get("description", "")) if renderer else node_config.get("description", "")
        approver = renderer.render(node_config.get("approver", "")) if renderer else node_config.get("approver", "")
        approval_type = node_config.get("approval_type", "approve_reject")
        timeout = node_config.get("timeout", 86400)

        approval_data = {
            "id": approval_id,
            "node_id": node.get("id", ""),
            "title": title,
            "description": description,
            "approver": approver,
            "approval_type": approval_type,
            "timeout": timeout,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
            "resolved_by": None,
            "resolution": None,
        }

        logger.info("WaitExecutor (manual_approval): node %s — created approval %s: %s", node_id, approval_id, title)

        return ExecutionResult(
            success=True,
            status="skipped",
            updated_context={
                "_halt": "approval",
                "_halt_node_id": node.get("id", ""),
                "approval_id": approval_id,
                "_approval_data": approval_data,
            },
            output={
                "wait_type": "manual_approval",
                "approval_id": approval_id,
                "title": title,
                "approver": approver,
                "status": "pending",
            },
        )

    def _execute_event_wait(
        self, wait_type, node_config, running_instance, lead_id, context, node_id, started_at,
    ) -> ExecutionResult:
        wait_condition = {
            "type": wait_type,
            "started_at": started_at.isoformat(),
        }
        if wait_type == "replied":
            wait_condition["channel"] = node_config.get("channel", "whatsapp")
            description = f"Wait until lead replied ({wait_condition['channel']})"
            # Optional timeout — every existing "replied" Wait node has no
            # "timeout" key at all, so wait_condition gets no
            # "timeout_seconds" key either and wait_condition_service.py
            # waits forever for a reply, exactly as before. Only a node that
            # explicitly opts in (e.g. a two-branch replied/timeout-next-node
            # Wait — see ExecutionEngine._resume_from) gets this key.
            timeout_duration = node_config.get("timeout")
            timeout_unit = node_config.get("timeout_unit", "minutes")
            if timeout_duration:
                wait_condition["timeout_seconds"] = timeout_duration * UNIT_SECONDS.get(timeout_unit, 60)
                description += f", or after {timeout_duration} {timeout_unit} with no reply"
        elif wait_type == "webhook_event":
            wait_condition["event_key"] = node_config.get("event_key", "")
            description = f"Wait until external event '{wait_condition['event_key']}'"
        else:  # stage_changed / field_condition
            wait_condition["field"] = node_config.get("field", "")
            wait_condition["operator"] = node_config.get("operator", "equals")
            wait_condition["value"] = node_config.get("value", "")
            description = (
                f"Wait until {wait_condition['field']} {wait_condition['operator']} {wait_condition['value']}"
            )

        logger.info(
            "WaitExecutor: event wait scheduled lead_id=%s node_id=%s wait_condition=%s",
            lead_id, node_id, wait_condition,
        )

        output_data = {
            "wait_type": wait_type,
            "wait_condition": wait_condition,
            "message": description,
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
            updated_context={"_wait_condition": wait_condition, "_wait": True},
            status="skipped",
            output=output,
        )
