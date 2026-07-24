"""Condition node executor.

Evaluates runtime conditions using ``{{variable}}`` resolution and a
comparison engine that supports equals, not_equals, greater_than,
less_than, contains, starts_with, and ends_with operators.

Configuration (node.config):
    field (str): The variable path to evaluate, e.g. ``lead.stage``.
    operator (str): Comparison operator (equals, not_equals, greater_than,
                    less_than, contains, starts_with, ends_with).
    value (str): The value to compare against.
    true_next_node_id (str): Node ID to route to when condition is TRUE.
    false_next_node_id (str): Node ID to route to when condition is FALSE.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload, record_audit_failure

logger = logging.getLogger(__name__)


_COMPARATORS = {}


def _register(op):
    """Decorator to register a comparison function."""
    def wrapper(fn):
        _COMPARATORS[op] = fn
        return fn
    return wrapper


@_register("equals")
def _equals(field_val, compare_val):
    return str(field_val).lower() == str(compare_val).lower()


@_register("not_equals")
def _not_equals(field_val, compare_val):
    return str(field_val).lower() != str(compare_val).lower()


@_register("greater_than")
def _greater_than(field_val, compare_val):
    try:
        return float(field_val) > float(compare_val)
    except (TypeError, ValueError):
        return str(field_val) > str(compare_val)


@_register("less_than")
def _less_than(field_val, compare_val):
    try:
        return float(field_val) < float(compare_val)
    except (TypeError, ValueError):
        return str(field_val) < str(compare_val)


@_register("contains")
def _contains(field_val, compare_val):
    return str(compare_val).lower() in str(field_val).lower()


@_register("starts_with")
def _starts_with(field_val, compare_val):
    return str(field_val).lower().startswith(str(compare_val).lower())


@_register("ends_with")
def _ends_with(field_val, compare_val):
    return str(field_val).lower().endswith(str(compare_val).lower())


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
        exec_ctx: Any = None,
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_config = node.get("config") or {}
        node_id = node.get("id", "condition")

        field = node_config.get("field", "")
        operator = node_config.get("operator", "equals")
        value = node_config.get("value", "")

        # ── Resolve the field value from ExecutionContext via renderer ──
        # field_resolved distinguishes "the variable genuinely has no value
        # anywhere the execution engine can see" (renderer/resolver both
        # returned None) from "the variable resolved to something, it just
        # didn't match" — only the former is a configuration/data problem
        # that must halt the node (see the fail-safe branch below); a
        # correctly-resolving field that simply evaluates False is normal.
        field_value = None
        field_resolved = False
        if exec_ctx and field:
            renderer = getattr(exec_ctx, "renderer", None)
            if renderer:
                resolved = renderer.render(f"{{{{{field}}}}}")
                if resolved != f"{{{{{field}}}}}":
                    field_value = resolved
                    field_resolved = True
                else:
                    path_value = renderer.resolve_path(field)
                    if path_value is not None:
                        field_value = path_value
                        field_resolved = True

        logger.info(
            "ConditionExecutor: node=%s lead=%s field=%r operator=%r expected_value=%r "
            "resolved=%s actual_value=%r",
            node_id, lead_id, field, operator, value, field_resolved, field_value,
        )

        # ── Fail-safe: never guess a branch for a node with no usable
        # config or a field the engine cannot actually resolve. Prior
        # behavior silently fell back to comparing the field's own raw
        # path string (e.g. "lead.replied" == "true" -> always False) and
        # continued as if that were a real evaluation — which is exactly
        # what let an unconfigured/unresolvable Condition node silently
        # choose the "false" branch (a real WhatsApp send) every time,
        # regardless of what actually happened for the lead.
        if not field or not field_resolved:
            reason = "missing_condition_field" if not field else "unresolvable_condition_field"
            error_message = (
                f"Condition node has no usable field to evaluate (field={field!r}) — "
                f"refusing to guess a branch"
                if not field else
                f"Condition field {field!r} did not resolve to any value in the execution "
                f"context (lead/company/journey/execution/today/now) — refusing to guess a branch"
            )
            logger.warning(
                "ConditionExecutor: %s — lead=%s node=%s field=%r operator=%r value=%r — "
                "halting node rather than silently choosing a branch",
                error_message, lead_id, node_id, field, operator, value,
            )
            await record_audit_failure(
                getattr(exec_ctx, "session", None) if exec_ctx else None,
                lead_id=lead_id,
                node_id=node_id,
                running_instance_id=str(running_instance.id),
                journey_id=getattr(running_instance, "journey_id", None),
                payload={
                    "reason": reason,
                    "field": field,
                    "operator": operator,
                    "value": value,
                    "timestamp": started_at.isoformat(),
                },
            )
            output_data = {
                "condition_result": None,
                "field": field,
                "resolved_field_value": None,
                "operator": operator,
                "value": value,
                "message": error_message,
            }
            output = {
                "log_payload": build_log_payload(
                    flow_definition_id=context.get("flow_definition_id", ""),
                    running_instance_id=str(running_instance.id),
                    lead_id=lead_id,
                    node_id=node_id,
                    node_type=self.node_type,
                    status="failed",
                    input_data={"condition": node_config},
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

        # ── Evaluate condition ───────────────────────────────────────
        comparators = _COMPARATORS
        compare_fn = comparators.get(operator)
        if compare_fn is None:
            logger.warning("ConditionExecutor: unknown operator %s for node %s", operator, node_id)
            condition_result = False
        else:
            try:
                condition_result = compare_fn(field_value, value)
            except Exception as exc:
                logger.error("ConditionExecutor: comparison error %s for node %s", exc, node_id)
                condition_result = False

        next_node_id: Optional[str] = None
        if condition_result:
            next_node_id = node_config.get("true_next_node_id")
        else:
            next_node_id = node_config.get("false_next_node_id")

        branch_label = "true" if condition_result else "false"
        if next_node_id:
            logger.info(
                "ConditionExecutor: node=%s lead=%s result=%s -> taking '%s' branch (next_node_id=%s)",
                node_id, lead_id, condition_result, branch_label, next_node_id,
            )
        else:
            logger.warning(
                "ConditionExecutor: node=%s lead=%s result=%s -> '%s' branch has no configured "
                "next_node_id; traversal will fall back to full graph adjacency for this node "
                "(see FlowValidationService, which now rejects this at publish time)",
                node_id, lead_id, condition_result, branch_label,
            )

        output_data = {
            "condition_result": condition_result,
            "field": field,
            "resolved_field_value": str(field_value),
            "operator": operator,
            "value": value,
            "branch_taken": branch_label,
            "next_node_id": next_node_id,
            "message": f"Condition evaluated to {condition_result} -> '{branch_label}' branch",
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
                input_data={"condition": node_config},
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
