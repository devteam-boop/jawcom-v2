"""Notification node executor.

Resolves ``{{variable}}`` placeholders in title and message (never rewritten
or summarized beyond that substitution), builds the JAWIS notification
payload, and delegates dispatching to :class:`NotificationIntegration
<app.integrations.NotificationIntegration>` (aliased to the real JAWIS
integration by default — see app/integrations/factory.py).

Configuration (node.config):
    title (str): Notification title (supports ``{{variable}}``).
    message (str): Notification body message (supports ``{{variable}}``).
    priority (str, optional): Defaults to "normal" — no Journey Builder UI
        field exists for this yet.
    assigned_to (str, optional): Defaults to the resolved lead's agent_name
        when not explicitly configured.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.integrations import IntegrationFactory
from app.integrations.jawis_communication import JawisCommunicationError
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload, record_audit_failure

logger = logging.getLogger(__name__)

# In-process retry/backoff before a Notification-node failure is reported
# (Part 3: "If Notification API fails: Retry. Mark node Failed."). Mirrors
# the existing JAWIS-webhook retry/backoff convention in
# communication_event_service.py's _publish_to_jawis (1 initial attempt + 3
# retries at increasing delays).
_RETRY_DELAYS_SECONDS = [1, 5, 15]


class NotificationExecutor(BaseNodeExecutor):
    """Executor for flow notification nodes."""

    @property
    def node_type(self) -> str:
        return "notification"

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
        node_id = node.get("id", "notification")

        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None
        raw_title = node_config.get("title", "")
        raw_message = node_config.get("message", "")

        # Title/message are rendered ({{variable}} substitution only) — the
        # designer's saved text is never rewritten or summarized.
        resolved_title = renderer.render(raw_title) if renderer else raw_title
        resolved_message = renderer.render(raw_message) if renderer else raw_message

        lead = (getattr(exec_ctx, "lead", None) if exec_ctx else None) or {}
        journey_name = getattr(exec_ctx, "journey_name", "") if exec_ctx else ""
        journey_id = getattr(running_instance, "journey_id", None)
        priority = node_config.get("priority") or "normal"
        assigned_to = node_config.get("assigned_to") or lead.get("agent_name")
        created_at = started_at.isoformat()

        logger.info(
            "NotificationExecutor: resolved notification for lead=%s node=%s title=%s",
            lead_id, node_id, resolved_title,
        )

        # ── Build the JAWIS notification payload ───────────────────
        request_payload = {
            "title": resolved_title,
            "message": resolved_message,
            "lead_id": lead_id,
            "journey_id": journey_id,
            "journey_name": journey_name,
            "node_id": node_id,
            "priority": priority,
            "assigned_to": assigned_to,
            "created_at": created_at,
        }

        integration = IntegrationFactory.get("notification")
        session = getattr(exec_ctx, "session", None) if exec_ctx else None

        integration_response = None
        last_error: Optional[Exception] = None
        for attempt, delay in enumerate([0, *_RETRY_DELAYS_SECONDS]):
            if delay:
                await asyncio.sleep(delay)
            try:
                integration_response = await integration.execute(request_payload)
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "NotificationExecutor: JAWIS notification attempt %s/%s failed for "
                    "lead=%s node=%s: %s",
                    attempt + 1, len(_RETRY_DELAYS_SECONDS) + 1, lead_id, node_id, exc,
                )

        if last_error is not None:
            error_message = f"JAWIS notification send failed after retries: {last_error}"
            logger.error(
                "NotificationExecutor: %s — lead=%s node=%s",
                error_message, lead_id, node_id,
            )
            await record_audit_failure(
                session,
                lead_id=lead_id,
                node_id=node_id,
                running_instance_id=str(running_instance.id),
                journey_id=journey_id,
                payload={
                    "reason": "jawis_notification_api_failure",
                    "notification_payload": request_payload,
                    "error": str(last_error),
                    "timestamp": created_at,
                },
            )
            # Raise (rather than return success=False) — matches the
            # existing ADR-017 convention already used by
            # JawisWhatsAppIntegration/JawisEmailIntegration: the engine's
            # existing exception handler in _execute_node() marks the
            # node/instance Failed with no further change needed here.
            raise JawisCommunicationError(error_message) from last_error

        output_data = {
            "message": resolved_message or "Notification sent",
            "resolved_title": resolved_title,
            "resolved_message": resolved_message,
            "raw_title": raw_title,
            "raw_message": raw_message,
            "notification_payload": request_payload,
            "provider_response": integration_response,
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"notification_config": node_config},
                output_data=output_data,
                started_at=started_at,
            ),
            **output_data,
        }

        return ExecutionResult(
            success=True,
            updated_context=context,
            status="success",
            output=output,
        )
