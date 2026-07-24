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

from app.config.settings import get_settings
from app.integrations import IntegrationFactory
from app.services.journey_send_idempotency_service import check_and_reserve, compute_dedup_key
from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload, record_audit_failure

logger = logging.getLogger(__name__)

# JAWIS notification-integration variable contract (lead_new journey): a
# WhatsApp template with exactly 4 positional variables ({{1}}..{{4}}) is
# assumed to follow this fixed, JAWIS-given field order. Gated on variable
# COUNT (not template id/name) so it can never affect any other journey's
# 1-3-variable template — those keep using the pre-existing name/phone/email
# fallback below, unchanged. Values always come from the resolved JAWIS lead
# context (exec_ctx.lead); never fabricated — a missing field fails the node
# instead of silently sending a guess (see the missing-variable branch below).
_JAWIS_FOUR_VARIABLE_FIELD_ORDER = ["first_name", "building_name", "city", "agent_name"]

# Per-template JAWIS field order for every other published production
# journey's WhatsApp template (Follow-Up, Qualified, Tour Scheduled,
# Proposal Sent, Won, Lost — Negotiation is notification-only, no WhatsApp
# template). Keyed by the resolved Meta template name (case-insensitive),
# so — unlike the lead_new heuristic above — templates that happen to share
# a variable count (e.g. scheduled_tour_confirm and lead_new are both
# 4-variable) each get their own explicit, unambiguous mapping instead of
# being conflated. Same contract as lead_new: values always come from the
# resolved JAWIS lead context, never fabricated; a missing field fails the
# node rather than guessing (see the missing-variable branch below).
#
# Keys are the exact `whatsapp_templates.template_name` values as synced
# from Meta (verified against the live templates referenced by each
# journey's flow) — every key below was previously a near-miss (e.g.
# "tour_confirm" vs the real "scheduled_tour_confirm") that never matched,
# which silently fell through to the wrong fallback heuristic below instead
# of resolving semantically.
_JAWIS_TEMPLATE_VARIABLE_MAP: Dict[str, list] = {
    # Follow-Up
    "contacted_req_noted": ["first_name", "seats", "building_name"],
    "lead_contacted_nudge_1": ["first_name", "building_name"],
    # Qualified / Options Shared
    "lead_qualified_option_share": ["seats", "building_name", "options_link"],
    # Site Visit Scheduled
    "scheduled_tour_confirm": ["building_name", "tour_datetime", "map_link", "agent_name"],
    "scheduled_remind24h": ["tour_datetime", "building_name"],
    "scheduled_remind_2h": ["tour_datetime", "building_name"],
    # Proposal Shared
    "lead_proposal_wa": ["plan_type", "building_name", "proposal_link", "move_in_date", "price"],
    "lead_proposal_followup": ["first_name", "building_name"],
    # Won
    "lead_won": ["plan_type", "building_name", "move_in_date"],
    # Lost
    "lead_lost_graceful_close": ["first_name"],
    "lead_lost_reengage": ["first_name", "building_name"],
}


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

        template = None
        template_declared_variables = []
        if template_id and template_service:
            template = await template_service.get_template(UUID(template_id))
            resolved_template = template.name
            template_declared_variables = template.variables or []
        else:
            resolved_template = renderer.render(template_name) if renderer else template_name

        resolved_variables = renderer.render_all(raw_variables) if renderer else raw_variables

        rendered_body_preview = None
        jawis_variable_resolution_used = False

        # The Journey Builder has no UI yet for mapping a template's
        # positional {{1}}/{{2}} variables to lead fields (node.config never
        # has a "variables" key), so raw_variables is always {} for a
        # template with declared variables — an explicit (even empty) config
        # always wins over every branch below.
        mapped_fields = _JAWIS_TEMPLATE_VARIABLE_MAP.get((resolved_template or "").strip().lower())

        if not resolved_variables and mapped_fields and len(template_declared_variables) == len(mapped_fields):
            # Named-template JAWIS resolution for every production journey
            # beyond lead_new (Follow-Up/Qualified/Tour Scheduled/Proposal
            # Sent/Won/Lost) — same contract as the lead_new branch below
            # (log every {{n}} -> value pair, refuse to send rather than
            # guess if any is missing), just keyed by the template's own
            # name instead of a fixed variable count, so e.g. tour_confirm
            # (4 variables) never collides with lead_new's own 4-variable
            # mapping just below.
            jawis_variable_resolution_used = True
            resolved_lead_for_vars = (getattr(exec_ctx, "lead", None) if exec_ctx else None) or {}
            jawis_values = [resolved_lead_for_vars.get(field) for field in mapped_fields]

            for position, field_name, value in zip(template_declared_variables, mapped_fields, jawis_values):
                logger.info(
                    "SendWhatsAppExecutor: {{%s}} -> %s (JAWIS field=%s) lead=%s node=%s template=%s",
                    position, value, field_name, lead_id, node_id, resolved_template,
                )

            missing_variables = [
                field_name for field_name, value in zip(mapped_fields, jawis_values)
                if not value
            ]

            if missing_variables:
                error_message = (
                    f"Missing required JAWIS variable(s) for WhatsApp template: {', '.join(missing_variables)}"
                )
                logger.error(
                    "SendWhatsAppExecutor: %s — lead=%s node=%s template=%s — send aborted, "
                    "never sending with an incomplete/guessed variable",
                    error_message, lead_id, node_id, resolved_template,
                )
                partial_resolved = {
                    field_name: value
                    for field_name, value in zip(mapped_fields, jawis_values)
                    if value
                }
                await record_audit_failure(
                    getattr(exec_ctx, "session", None) if exec_ctx else None,
                    lead_id=lead_id,
                    node_id=node_id,
                    running_instance_id=str(running_instance.id),
                    journey_id=getattr(running_instance, "journey_id", None),
                    payload={
                        "reason": "missing_jawis_variable",
                        "missing_variables": missing_variables,
                        "resolved_variables_partial": partial_resolved,
                        "template_id": template_id,
                        "template_name": resolved_template,
                        "timestamp": started_at.isoformat(),
                    },
                )
                output_data = {
                    "message": error_message,
                    "resolved_template_name": resolved_template,
                    "missing_variables": missing_variables,
                    "resolved_variables_partial": partial_resolved,
                    "template_id": template_id,
                    "status": "failed_missing_variable",
                }
                output = {
                    "log_payload": build_log_payload(
                        flow_definition_id=context.get("flow_definition_id", ""),
                        running_instance_id=str(running_instance.id),
                        lead_id=lead_id,
                        node_id=node_id,
                        node_type=self.node_type,
                        status="failed",
                        input_data={"template_id": template_id, "template_name": template_name},
                        output_data=output_data,
                        error_message=error_message,
                        started_at=started_at,
                    ),
                    **output_data,
                }
                return ExecutionResult(
                    success=False,
                    updated_context=context,
                    status="failed",
                    error=error_message,
                    output=output,
                )

            resolved_variables = dict(zip(template_declared_variables, jawis_values))
        elif not resolved_variables and len(template_declared_variables) == 4:
            # JAWIS notification integration: a 4-variable template is
            # assumed to be the lead_new-shaped template — resolve strictly
            # from JAWIS-sourced lead fields, log every {{n}} -> value pair,
            # and refuse to send (rather than guess) if any is missing.
            jawis_variable_resolution_used = True
            resolved_lead_for_vars = (getattr(exec_ctx, "lead", None) if exec_ctx else None) or {}
            jawis_values = [resolved_lead_for_vars.get(field) for field in _JAWIS_FOUR_VARIABLE_FIELD_ORDER]

            for position, field_name, value in zip(
                template_declared_variables, _JAWIS_FOUR_VARIABLE_FIELD_ORDER, jawis_values,
            ):
                logger.info(
                    "SendWhatsAppExecutor: {{%s}} -> %s (JAWIS field=%s) lead=%s node=%s",
                    position, value, field_name, lead_id, node_id,
                )

            missing_variables = [
                field_name for field_name, value in zip(_JAWIS_FOUR_VARIABLE_FIELD_ORDER, jawis_values)
                if not value
            ]

            if missing_variables:
                error_message = (
                    f"Missing required JAWIS variable(s) for WhatsApp template: {', '.join(missing_variables)}"
                )
                logger.error(
                    "SendWhatsAppExecutor: %s — lead=%s node=%s template=%s — send aborted, "
                    "never sending with an incomplete/guessed variable",
                    error_message, lead_id, node_id, resolved_template,
                )
                partial_resolved = {
                    field_name: value
                    for field_name, value in zip(_JAWIS_FOUR_VARIABLE_FIELD_ORDER, jawis_values)
                    if value
                }
                await record_audit_failure(
                    getattr(exec_ctx, "session", None) if exec_ctx else None,
                    lead_id=lead_id,
                    node_id=node_id,
                    running_instance_id=str(running_instance.id),
                    journey_id=getattr(running_instance, "journey_id", None),
                    payload={
                        "reason": "missing_jawis_variable",
                        "missing_variables": missing_variables,
                        "resolved_variables_partial": partial_resolved,
                        "template_id": template_id,
                        "template_name": resolved_template,
                        "timestamp": started_at.isoformat(),
                    },
                )
                output_data = {
                    "message": error_message,
                    "resolved_template_name": resolved_template,
                    "missing_variables": missing_variables,
                    "resolved_variables_partial": partial_resolved,
                    "template_id": template_id,
                    "status": "failed_missing_variable",
                }
                output = {
                    "log_payload": build_log_payload(
                        flow_definition_id=context.get("flow_definition_id", ""),
                        running_instance_id=str(running_instance.id),
                        lead_id=lead_id,
                        node_id=node_id,
                        node_type=self.node_type,
                        status="failed",
                        input_data={"template_id": template_id, "template_name": template_name},
                        output_data=output_data,
                        error_message=error_message,
                        started_at=started_at,
                    ),
                    **output_data,
                }
                return ExecutionResult(
                    success=False,
                    updated_context=context,
                    status="failed",
                    error=error_message,
                    output=output,
                )

            resolved_variables = dict(zip(template_declared_variables, jawis_values))
        elif not resolved_variables and template_declared_variables:
            # Legacy fallback for any non-4-variable template — unchanged
            # from before: the one mapping convention every such WhatsApp
            # template observed so far uses ({{1}} = recipient name) rather
            # than sending a template with unrendered placeholders.
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

        if template is not None and template.content:
            rendered_body_preview = template.content
            for position, value in resolved_variables.items():
                rendered_body_preview = rendered_body_preview.replace(f"{{{{{position}}}}}", str(value))

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
            try:
                is_duplicate = await check_and_reserve(session, dedup_key, lead_id=lead_id, node_id=node_id)
            except Exception:
                # A dedup mechanism must never block a send if its own table
                # is unavailable (e.g. journey_send_idempotency missing) —
                # log and proceed as if this were a fresh (non-duplicate)
                # send. Roll back first: the failed statement left the
                # session's transaction aborted, which would otherwise break
                # every later query on this same session (e.g. logging).
                logger.warning(
                    "SendWhatsAppExecutor: idempotency check failed (journey_send_idempotency "
                    "table missing or unavailable) — proceeding with send for lead=%s node=%s",
                    lead_id, node_id, exc_info=True,
                )
                await session.rollback()
                is_duplicate = False
            if is_duplicate:
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
                    # Same routing metadata append as the success path below
                    # — this still becomes a whatsapp_sent CommunicationEvent
                    # (engine.py records one for any result.success, and a
                    # suppressed duplicate is success=True), so it needs the
                    # same "to" for phone-based reply matching to find it.
                    # No provider_message_id: no Meta call happens on this
                    # path (suppressed before the integration call).
                    "to": request_payload.get("recipient_phone"),
                    "from": get_settings().WHATSAPP_PHONE_NUMBER_ID,
                    "provider_message_id": None,
                    "template_name": resolved_template,
                    "channel": "whatsapp",
                    "direction": "outbound",
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
            # Audit-only local preview of the substituted body text (Meta
            # still performs the real substitution server-side) — Part 4
            # ("Store ... rendered template ...").
            "rendered_body_preview": rendered_body_preview,
            "jawis_variable_resolution_used": jawis_variable_resolution_used,
            # Routing metadata — appended (never overwrites any key above).
            # Manual sends (app/api/message_routes.py) have always stored
            # "to"/"from" on their CommunicationEvent payload; automation
            # sends never did, which made every automation-sent
            # whatsapp_sent row invisible to
            # CommunicationEventRepository.get_latest_whatsapp_sent_by_phone/
            # get_whatsapp_sent_candidates_by_phone (both match on
            # payload->>'to', and SQL "NULL = x" is never true) — a reply
            # could then only ever be attributed to whichever OTHER lead's
            # manually-sent row happened to still be findable for that
            # phone number, even after the number moved to a different
            # lead entirely. "to" is the destination phone actually used
            # for this Meta send (same value as request_payload's
            # recipient_phone, not re-derived); "from" mirrors the same
            # settings.WHATSAPP_PHONE_NUMBER_ID manual sends use.
            "to": request_payload.get("recipient_phone"),
            "from": get_settings().WHATSAPP_PHONE_NUMBER_ID,
            "provider_message_id": integration_response.get("provider_message_id"),
            "template_name": resolved_template,
            "channel": "whatsapp",
            "direction": "outbound",
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
