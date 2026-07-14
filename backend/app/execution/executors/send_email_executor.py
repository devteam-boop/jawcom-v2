"""Send Email node executor.

Resolves ``template_id`` to a real template (via ``exec_ctx.template_service``),
renders ``{{variable}}`` placeholders in subject and body, and delegates
sending to :class:`EmailIntegration <app.integrations.EmailIntegration>`.

Configuration (node.config):
    subject (str): Email subject line (supports ``{{variable}}``). Falls
        back to the resolved template's own subject when left blank.
    template_id (str): ID of the Template row to send (preferred).
    template_name (str): Free-text template name — legacy fallback, used
        only when ``template_id`` is absent.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from app.integrations import IntegrationFactory
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class SendEmailExecutor(BaseNodeExecutor):
    """Executor for flow send_email nodes."""

    @property
    def node_type(self) -> str:
        return "send_email"

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
        node_id = node.get("id", "send_email")

        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None
        template_service = getattr(exec_ctx, "template_service", None) if exec_ctx else None
        raw_subject = node_config.get("subject", "")
        template_id = node_config.get("template_id")
        template_name = node_config.get("template_name", "")

        resolved_content = None
        if template_id and template_service:
            template = await template_service.get_template(UUID(template_id))
            resolved_template = template.name
            subject_source = raw_subject or template.subject or ""
            resolved_content = renderer.render(template.content) if renderer else template.content
        else:
            resolved_template = renderer.render(template_name) if renderer else template_name
            subject_source = raw_subject

        resolved_subject = renderer.render(subject_source) if renderer else subject_source

        logger.info(
            "SendEmailExecutor: resolved email for lead=%s node=%s subject=%s "
            "template_id=%s template=%s",
            lead_id, node_id, resolved_subject, template_id, resolved_template,
        )

        await asyncio.sleep(0.1)

        # ── Build integration request ──────────────────────────────
        # exec_ctx.lead is already resolved by the engine for this node (no
        # extra lookup) — recipient_email/recipient_name are included so
        # that if the "email" alias ever points at email_resend
        # (JAWIS_EMAIL_PROVIDER=resend), that integration has what it needs
        # without performing its own lead lookup. JawisEmailIntegration (the
        # default target) forwards the whole payload to JAWIS verbatim
        # (requires "lead_id" as a string and "body", mirroring the manual
        # contract in app/api/message_routes.py), so recipient_email/
        # recipient_name are a no-op for that default path.
        resolved_lead = getattr(exec_ctx, "lead", None) if exec_ctx else None
        recipient_email = (resolved_lead or {}).get("email")

        # Lead genuinely has no email on file (not a lookup failure — Bug 1's
        # fix already made this field real data, not a fabricated null) —
        # fail this node clearly, same as manual send's 400 "has no email
        # address on file" (app/api/message_routes.py send_email()), instead
        # of reaching JAWIS with a null recipient.
        if not recipient_email:
            logger.warning(
                "SendEmailExecutor: lead=%s has no email address on file — failing node %s instead of sending",
                lead_id, node_id,
            )
            return ExecutionResult(
                success=False,
                status="failed",
                error=f"Lead {lead_id} has no email address on file",
            )

        request_payload = {
            "subject": resolved_subject,
            "template_name": resolved_template,
            "body": resolved_content,
            "lead_id": str(getattr(running_instance, "lead_id", lead_id)),
            "recipient_email": recipient_email,
            "recipient_name": (resolved_lead or {}).get("name"),
        }
        integration = IntegrationFactory.get("email")
        integration_response = await integration.execute(request_payload)

        output_data = {
            "message": f"Email resolved (subject: {resolved_subject})",
            "resolved_subject": resolved_subject,
            "resolved_template_name": resolved_template,
            "resolved_content": resolved_content,
            "template_id": template_id,
            "raw_subject": raw_subject,
            "raw_template_name": template_name,
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
                input_data={"subject": raw_subject, "template_id": template_id, "template_name": template_name},
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
