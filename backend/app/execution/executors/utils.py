"""Execution framework shared helpers.

This module provides a thin logging helper used by all executors to create
Started / Completed / Failed execution logs in a consistent format without
embedding log-service knowledge inside concrete executors.

The actual persistence is handled by the ExecutionEngine using the public
FlowExecutionLogCreateSchema.
"""

import time
from datetime import datetime
from typing import Any, Dict, Optional


def build_log_payload(
    *,
    flow_definition_id: str,
    running_instance_id: str,
    lead_id: int,
    node_id: str,
    node_type: str,
    status: str,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    duration_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """Return a dictionary compatible with FlowExecutionLogCreateSchema.

    Args:
        flow_definition_id: UUID string of the active flow definition.
        running_instance_id: UUID string of the running instance.
        lead_id: Lead identifier.
        node_id: Flow node identifier.
        node_type: Type of the executed node.
        status: "started", "success", "failed", or "skipped".
        input_data: Node input snapshot.
        output_data: Node output snapshot.
        error_message: Error details when status is failed.
        started_at: Timestamp when execution started.
        completed_at: Timestamp when execution finished.
        duration_ms: Wall-clock duration in milliseconds.

    Returns:
        Dict that can be unpacked into FlowExecutionLogCreateSchema.
    """
    now = datetime.utcnow()
    resolved_started_at = started_at or now
    resolved_completed_at = completed_at or now
    resolved_duration = duration_ms
    if resolved_duration is None and started_at is not None:
        resolved_duration = int(
            (resolved_completed_at - started_at).total_seconds() * 1000
        )

    return {
        "flow_definition_id": flow_definition_id,
        "running_instance_id": running_instance_id,
        "lead_id": lead_id,
        "node_id": node_id,
        "status": status,
        "input": {
            "node_type": node_type,
            "started_at": resolved_started_at.isoformat(),
            **(input_data or {}),
        },
        "output": {
            "completed_at": resolved_completed_at.isoformat(),
            **(output_data or {}),
        },
        "error_message": error_message,
        "duration_ms": resolved_duration,
    }


def get_next_node_id(node: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
    """Resolve the default next node from a flow node definition.

    Prefer an explicit ``next_node_id`` stored in node config (used by
    condition branches) otherwise return None and let the engine use graph
    adjacency.
    """
    node_config = node.get("config") or {}
    return node_config.get("next_node_id") or None


async def record_audit_failure(
    session: Any,
    *,
    lead_id: int,
    node_id: str,
    running_instance_id: str,
    journey_id: Optional[str],
    payload: Dict[str, Any],
) -> None:
    """Write a FAILED CommunicationEvent for audit purposes, best-effort.

    The engine's own failure-log path (ExecutionEngine._create_failed_log)
    only persists a plain string ``error_message`` onto FlowExecutionLog, not
    an executor's structured output — so an executor that needs to record
    *why* it failed (which variable was missing, the last provider error, a
    partial payload, a timestamp) writes it here directly instead, reusing
    CommunicationEvent's existing FAILED type (see that model's docstring:
    "the outbound send itself failed ... recorded directly by the send
    endpoint"). This also gets the existing JAWIS sync for free (`"failed"`
    is already in communication_event_service.py's outbound event-type set).

    Never raises — an audit-write failure must never mask the real failure
    the caller is already reporting via its ExecutionResult/exception.
    """
    if session is None:
        return
    try:
        from app.services.communication_event_service import CommunicationEventService
        from app.communication_events.schemas import CommunicationEventCreateSchema
        from app.models.communication_event import CommunicationEventType, CommunicationEventChannel

        await CommunicationEventService(session).create(
            CommunicationEventCreateSchema(
                running_instance_id=running_instance_id,
                journey_id=journey_id,
                lead_id=lead_id,
                node_id=node_id,
                event_type=CommunicationEventType.FAILED.value,
                channel=CommunicationEventChannel.SYSTEM.value,
                payload=payload,
            )
        )
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "record_audit_failure: failed to write audit CommunicationEvent for node=%s instance=%s",
            node_id, running_instance_id,
        )
