"""Production Email Message API.

Standalone send endpoint — not tied to the Journey Engine or a flow node.
Reuses existing services only:
  - LeadProviderFactory (fetch lead + resolve recipient email)
  - TemplateService (fetch template, render via its own TemplateRenderer —
    no rendering logic is duplicated here)
  - the existing Resend integration ("email_resend", NOT the "email" alias,
    so this never resolves to JAWIS regardless of JAWIS_EMAIL_PROVIDER)
  - CommunicationEventService (EMAIL_SENT audit log)

``CommunicationEvent.running_instance_id`` is a required (non-nullable) FK
to ``running_journey_instances``, and that schema is not being changed.
This endpoint serves two callers:
  - Journey-originated sends, which pass ``context_id`` = a real
    running_instance_id -> an EMAIL_SENT event is recorded against it.
  - Manual/general sends (``module="general"``, ``context_id=None``), which
    have no running instance -> the email still sends, no event row is
    written, and ``communication_event_id`` is returned as ``null``.
This is temporary, production-compatible behavior until manual
communication is migrated onto the unified communication timeline.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.templates.services import TemplateService
from app.templates.exceptions import TemplateNotFoundError, TemplateValidationError
from app.integrations import IntegrationFactory, NativeProviderError
from app.execution.providers import LeadProviderFactory
from app.communication_events.schemas import CommunicationEventCreateSchema
from app.models.communication_event import CommunicationEventType, CommunicationEventChannel
from app.services.communication_event_service import CommunicationEventService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["Messages"])


class EmailSendRequest(BaseModel):
    lead_id: int
    template_key: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    module: str = "general"
    context_id: Optional[str] = None


class EmailSendResponse(BaseModel):
    success: bool
    status: str
    provider_message_id: Optional[str] = None
    communication_event_id: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    provider_response: Dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/email/send",
    response_model=EmailSendResponse,
    summary="Send a production email via the existing Resend integration",
)
async def send_email(
    request: EmailSendRequest,
    db: AsyncSession = Depends(get_db_session),
):
    # ── 1. Validate request ────────────────────────────────────────
    try:
        template_uuid = UUID(request.template_key)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid template_key: {request.template_key!r}")

    # ── 2/3. Fetch lead via the existing Lead Provider, resolve email ──
    lead_provider = LeadProviderFactory.get_provider()
    lead_context = await lead_provider.get_lead_context(request.lead_id)
    lead = (lead_context or {}).get("lead") or {}
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")

    recipient_email = lead.get("email")
    if not recipient_email:
        raise HTTPException(status_code=400, detail=f"Lead {request.lead_id} has no email address on file")

    # ── 4/5. Fetch + render template via the existing TemplateService ──
    template_service = TemplateService(db)
    try:
        template = await template_service.get_template(template_uuid)
    except TemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if template.channel != "email":
        raise HTTPException(
            status_code=400,
            detail=f"Template {request.template_key} is a '{template.channel}' template, not 'email'",
        )

    try:
        rendered = template_service.renderer.render_email(
            template.subject or "", template.content, request.variables
        )
    except TemplateValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # ── 6. Send via the existing Resend integration (never JAWIS) ──────
    integration = IntegrationFactory.get("email_resend")
    try:
        result = await integration.execute({
            "subject": rendered["subject"],
            "content": rendered["content"],
            "recipient": request.lead_id,
        })
    except NativeProviderError as exc:
        logger.warning("Email send failed for lead=%s template=%s: %s", request.lead_id, request.template_key, exc)
        return EmailSendResponse(
            success=False,
            status="failed",
            provider_message_id=None,
            communication_event_id=None,
            error=str(exc),
            provider="resend",
            provider_response={},
        )

    provider_message_id = result.get("provider_message_id")

    # ── 7. Record EMAIL_SENT only when a valid running_instance_id
    #        (context_id) exists — i.e. the request originated from a
    #        Journey. Manual/general sends (context_id=None) skip this
    #        by design; see module docstring. ──────────────────────────
    communication_event_id: Optional[str] = None
    if request.context_id:
        try:
            running_instance_id = str(UUID(request.context_id))
            event_service = CommunicationEventService(db)
            event = await event_service.create(
                CommunicationEventCreateSchema(
                    running_instance_id=running_instance_id,
                    lead_id=request.lead_id,
                    event_type=CommunicationEventType.EMAIL_SENT.value,
                    channel=CommunicationEventChannel.EMAIL.value,
                    provider="resend",
                    provider_message_id=provider_message_id,
                    payload={
                        "template_key": request.template_key,
                        "variables": request.variables,
                        "module": request.module,
                    },
                )
            )
            communication_event_id = event.id
        except (ValueError, IntegrityError) as exc:
            await db.rollback()
            logger.warning(
                "Could not record EMAIL_SENT for lead=%s context_id=%s: %s",
                request.lead_id, request.context_id, exc,
            )

    # ── 8. Return ───────────────────────────────────────────────────
    return EmailSendResponse(
        success=True,
        status=result.get("status", "sent"),
        provider_message_id=provider_message_id,
        communication_event_id=communication_event_id,
    )


class WhatsAppSendRequest(BaseModel):
    lead_id: int
    template_key: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    module: str = "general"
    context_id: Optional[str] = None


class WhatsAppSendResponse(BaseModel):
    success: bool
    status: str
    provider_message_id: Optional[str] = None
    communication_event_id: Optional[str] = None


@router.post(
    "/whatsapp/send",
    response_model=WhatsAppSendResponse,
    summary="Send a production WhatsApp message via the existing Meta integration",
)
async def send_whatsapp(
    request: WhatsAppSendRequest,
    db: AsyncSession = Depends(get_db_session),
):
    # ── 1. Validate request ────────────────────────────────────────
    try:
        template_uuid = UUID(request.template_key)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid template_key: {request.template_key!r}")

    # ── 2/3. Fetch lead via the existing Lead Provider, resolve phone ──
    lead_provider = LeadProviderFactory.get_provider()
    lead_context = await lead_provider.get_lead_context(request.lead_id)
    lead = (lead_context or {}).get("lead") or {}
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")

    recipient_phone = lead.get("phone")
    if not recipient_phone:
        raise HTTPException(status_code=400, detail=f"Lead {request.lead_id} has no phone number on file")

    # ── 4/5. Fetch + render template via the existing TemplateService ──
    template_service = TemplateService(db)
    try:
        template = await template_service.get_template(template_uuid)
    except TemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if template.channel != "whatsapp":
        raise HTTPException(
            status_code=400,
            detail=f"Template {request.template_key} is a '{template.channel}' template, not 'whatsapp'",
        )

    try:
        # Reuses the same TemplateRenderer instance TemplateService already
        # owns (mirrors render_email() above) — rendering logic itself is
        # not duplicated. The rendered body isn't sent directly: Meta's
        # WhatsApp Business API only accepts approved templates addressed
        # by name with positional parameters (see below), the same
        # contract SendWhatsAppExecutor already uses — this call exists to
        # validate the variables against the template before sending.
        template_service.renderer.render_whatsapp(template.content, request.variables)
    except TemplateValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # ── 6. Send via the existing Meta integration (never JAWIS) ────────
    integration = IntegrationFactory.get("whatsapp_meta")
    try:
        result = await integration.execute({
            "template_name": template.name,
            "variables": request.variables,
            "recipient": request.lead_id,
        })
    except NativeProviderError as exc:
        logger.warning("WhatsApp send failed for lead=%s template=%s: %s", request.lead_id, request.template_key, exc)
        return WhatsAppSendResponse(
            success=False,
            status="failed",
            provider_message_id=None,
            communication_event_id=None,
        )

    provider_message_id = result.get("provider_message_id")

    # ── 7. Record WHATSAPP_SENT only when a valid running_instance_id
    #        (context_id) exists — i.e. the request originated from a
    #        Journey. Manual/general sends (context_id=None) skip this
    #        by design; exactly mirrors the Email API. ──────────────────
    communication_event_id: Optional[str] = None
    if request.context_id:
        try:
            running_instance_id = str(UUID(request.context_id))
            event_service = CommunicationEventService(db)
            event = await event_service.create(
                CommunicationEventCreateSchema(
                    running_instance_id=running_instance_id,
                    lead_id=request.lead_id,
                    event_type=CommunicationEventType.WHATSAPP_SENT.value,
                    channel=CommunicationEventChannel.WHATSAPP.value,
                    provider="meta",
                    provider_message_id=provider_message_id,
                    payload={
                        "template_key": request.template_key,
                        "variables": request.variables,
                        "module": request.module,
                    },
                )
            )
            communication_event_id = event.id
        except (ValueError, IntegrityError) as exc:
            await db.rollback()
            logger.warning(
                "Could not record WHATSAPP_SENT for lead=%s context_id=%s: %s",
                request.lead_id, request.context_id, exc,
            )

    # ── 8. Return ───────────────────────────────────────────────────
    return WhatsAppSendResponse(
        success=True,
        status=result.get("status", "sent"),
        provider_message_id=provider_message_id,
        communication_event_id=communication_event_id,
    )
