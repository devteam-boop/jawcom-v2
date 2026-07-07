"""Condition node executor.

Evaluates runtime conditions using ``{{variable}}`` resolution and a
comparison engine that supports equals, not_equals, greater_than,
less_than, contains, starts_with, and ends_with operators.

Configuration (node.config):
    field (str): The variable path to evaluate, e.g. ``lead.stage_key``.
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
from .utils import build_log_payload

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

        # Resolve the field value from ExecutionContext via renderer
        field_value = None
        if exec_ctx and field:
            renderer = getattr(exec_ctx, "renderer", None)
            if renderer:
                resolved = renderer.render(f"{{{{{field}}}}}")
                field_value = resolved if resolved != f"{{{{{field}}}}}" else None
            if field_value is None and renderer:
                field_value = renderer.resolve_path(field)

        # Fallback: use raw field string
        if field_value is None:
            field_value = field

        # Evaluate condition
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

        output_data = {
            "condition_result": condition_result,
            "field": field,
            "resolved_field_value": str(field_value),
            "operator": operator,
            "value": value,
            "message": f"Condition evaluated to {condition_result}",
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
