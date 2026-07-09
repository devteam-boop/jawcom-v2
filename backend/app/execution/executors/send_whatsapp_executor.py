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

        if template_id and template_service:
            template = await template_service.get_template(UUID(template_id))
            resolved_template = template.name
        else:
            resolved_template = renderer.render(template_name) if renderer else template_name

        resolved_variables = renderer.render_all(raw_variables) if renderer else raw_variables

        logger.info(
            "SendWhatsAppExecutor: resolved template for lead=%s node=%s "
            "template_id=%s template=%s variables=%s",
            lead_id, node_id, template_id, resolved_template, resolved_variables,
        )

        await asyncio.sleep(0.1)

        # ── Build integration request ──────────────────────────────
        # exec_ctx.lead is already resolved by the engine for this node
        # (no extra lookup) — recipient_phone/recipient_name are included
        # alongside the existing recipient=lead_id so that if the
        # "whatsapp" alias ever points at whatsapp_meta
        # (JAWIS_WHATSAPP_PROVIDER=meta), that integration has what it
        # needs without performing its own lead lookup. JawisWhatsAppIntegration
        # (the default target) forwards the whole payload to JAWIS verbatim,
        # so these extra keys are a no-op for the default path.
        resolved_lead = getattr(exec_ctx, "lead", None) if exec_ctx else None
        request_payload = {
            "template_name": resolved_template,
            "variables": resolved_variables,
            "recipient": getattr(running_instance, "lead_id", lead_id),
            "recipient_phone": (resolved_lead or {}).get("phone"),
            "recipient_name": (resolved_lead or {}).get("name"),
        }
        integration = IntegrationFactory.get("whatsapp")
        integration_response = await integration.execute(request_payload)

        output_data = {
            "message": f"WhatsApp message resolved (template: {resolved_template})",
            "resolved_template_name": resolved_template,
            "resolved_variables": resolved_variables,
            "template_id": template_id,
            "raw_template_name": template_name,
            "raw_variables": raw_variables,
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
