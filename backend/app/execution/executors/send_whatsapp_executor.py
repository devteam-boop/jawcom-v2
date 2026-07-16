"""Send WhatsApp node executor.

Resolves ``template_id`` to a real template (via ``exec_ctx.template_service``),
renders ``{{variable}}`` placeholders, builds a request payload, and delegates
sending to :class:`WhatsAppIntegration <app.integrations.WhatsAppIntegration>`.

Configuration (node.config):
    template_id (str): ID of the Template row to send (preferred).
    template_name (str): Free-text template name — legacy fallback, used
        only when ``template_id`` is absent.
    variables (dict): Variable mappings for the template.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from app.integrations import IntegrationFactory
from app.services.journey_send_idempotency_service import check_and_reserve, compute_dedup_key
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class SendWhatsAppExecutor(BaseNodeExecutor):
    """Executor for flow send_whatsapp nodes."""

    @property
    def node_type(self) -> str:
        return "send_whatsapp"

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
        node_id = node.get("id", "send_whatsapp")

        renderer = getattr(exec_ctx, "renderer", None) if exec_ctx else None
        template_service = getattr(exec_ctx, "template_service", None) if exec_ctx else None
        template_id = node_config.get("template_id")
        template_name = node_config.get("template_name", "")
        raw_variables = node_config.get("variables", {})

        template_declared_variables = []
        if template_id and template_service:
            template = await template_service.get_template(UUID(template_id))
            resolved_template = template.name
            template_declared_variables = template.variables or []
        else:
            resolved_template = renderer.render(template_name) if renderer else template_name

        resolved_variables = renderer.render_all(raw_variables) if renderer else raw_variables

        # The Journey Builder has no UI yet for mapping a template's
        # positional {{1}}/{{2}} variables to lead fields (node.config never
        # has a "variables" key), so raw_variables is always {} for a
        # template with declared variables. Falls back to the one mapping
        # convention every WhatsApp template observed so far uses
        # ({{1}} = recipient name) rather than sending a template with
        # unrendered placeholders — only when the node genuinely configured
        # nothing, so an explicit (even empty) config always wins.
        if not resolved_variables and template_declared_variables:
            resolved_lead_for_vars = getattr(exec_ctx, "lead", None) if exec_ctx else None
            lead_field_defaults = [
                (resolved_lead_for_vars or {}).get("name"),
                (resolved_lead_for_vars or {}).get("phone"),
                (resolved_lead_for_vars or {}).get("email"),
            ]
            resolved_variables = {
                var_key: value
                for var_key, value in zip(template_declared_variables, lead_field_defaults)
                if value
            }

        logger.info(
            "SendWhatsAppExecutor: resolved template for lead=%s node=%s "
            "template_id=%s template=%s variables=%s",
            lead_id, node_id, template_id, resolved_template, resolved_variables,
        )

        await asyncio.sleep(0.1)

        # ── Build integration request ──────────────────────────────
        # Mirrors the manual-send contract (WhatsAppSendRequest in
        # app/api/message_routes.py: lead_id/template_name/language/stage/
        # variables/module/context_id). Sent straight to "whatsapp_meta"
        # (see below) — recipient_phone/recipient_name are what that
        # integration actually reads (exec_ctx.lead is already resolved by
        # the engine for this node, no extra lookup needed); the other keys
        # are extra context carried in the payload but unused by the Meta
        # send itself.
        resolved_lead = getattr(exec_ctx, "lead", None) if exec_ctx else None
        request_payload = {
            "lead_id": str(getattr(running_instance, "lead_id", lead_id)),
            "template_name": resolved_template,
            "language": node_config.get("language", "en_US"),
            "stage": context.get("trigger_stage_key"),
            "variables": resolved_variables,
            "module": "general",
            "context_id": str(running_instance.id),
            "recipient_phone": (resolved_lead or {}).get("phone"),
            "recipient_name": (resolved_lead or {}).get("name"),
        }
        # One journey step = one send: reserve (lead_id, node_id, template)
        # before calling JAWIS so a webhook replay that spins up a second
        # RunningJourneyInstance, or a node/journey retry that re-executes
        # this already-sent node, can't fire the same WhatsApp send twice.
        # exec_ctx.session is only unset for callers that don't go through
        # the engine (none in the live app) — skip the guard rather than
        # block the send in that case.
        session = getattr(exec_ctx, "session", None) if exec_ctx else None
        stage_at_send = context.get("trigger_stage_key")
        if session is not None:
            dedup_key = compute_dedup_key(lead_id, node_id, template_id or resolved_template)
            if await check_and_reserve(session, dedup_key, lead_id=lead_id, node_id=node_id):
                logger.warning(
                    "SendWhatsAppExecutor: duplicate send suppressed for lead=%s node=%s "
                    "template=%s (already reserved within the dedup window)",
                    lead_id, node_id, template_id or resolved_template,
                )
                output_data = {
                    "message": f"WhatsApp send skipped — duplicate of a recent send (template: {resolved_template})",
                    "resolved_template_name": resolved_template,
                    "resolved_variables": resolved_variables,
                    "template_id": template_id,
                    "raw_template_name": template_name,
                    "raw_variables": raw_variables,
                    "status": "skipped_duplicate",
                    "stage_at_send": stage_at_send,
                }
                output = {
                    "log_payload": build_log_payload(
                        flow_definition_id=context.get("flow_definition_id", ""),
                        running_instance_id=str(running_instance.id),
                        lead_id=lead_id,
                        node_id=node_id,
                        node_type=self.node_type,
                        status="skipped",
                        input_data={"template_id": template_id, "template_name": template_name},
                        output_data=output_data,
                        started_at=started_at,
                    ),
                    **output_data,
                }
                return ExecutionResult(
                    success=True,
                    updated_context=context,
                    status="skipped_duplicate",
                    output=output,
                )

        # Direct Meta Cloud API send — bypasses the "whatsapp" alias (and
        # therefore jawis_communication.py's relay to JAWIS) entirely, so
        # automation sends through the same transport as manual send
        # (app/api/message_routes.py, which already targets "whatsapp_meta").
        integration = IntegrationFactory.get("whatsapp_meta")
        integration_response = await integration.execute(request_payload)

        output_data = {
            "message": f"WhatsApp message resolved (template: {resolved_template})",
            "resolved_template_name": resolved_template,
            "resolved_variables": resolved_variables,
            "template_id": template_id,
            "raw_template_name": template_name,
            "raw_variables": raw_variables,
            "provider_response": integration_response,
            # Immutable snapshot of the stage that triggered this send — set
            # once, here, never re-derived downstream (see
            # CommunicationEventService._publish_to_jawis's "stage" field).
            "stage_at_send": stage_at_send,
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"template_id": template_id, "template_name": template_name},
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
