"""Production Email Message API.

Standalone send endpoint — not tied to the Journey Engine or a flow node.
Reuses existing services only:
  - JawisClient.get_lead() (lightweight lead lookup: id/name/email/phone/city
    only — NOT LeadProviderFactory/get_lead_context(), which requires
    stage_key and is reserved for Journey Engine execution; manual sends
    don't need stage/company/owner)
  - TemplateService (fetch template, render via its own TemplateRenderer —
    no rendering logic is duplicated here)
  - the existing Resend integration ("email_resend", NOT the "email" alias,
    so this never resolves to JAWIS regardless of JAWIS_EMAIL_PROVIDER)
  - CommunicationEventService (EMAIL_SENT audit log)

``CommunicationEvent.running_instance_id`` is nullable (migration
b4c5d6e7f8a9) so both callers below share the same table:
  - Journey-originated sends, which pass ``context_id`` = a real
    running_instance_id -> the EMAIL_SENT event is recorded with that id.
  - Manual/general sends (``module="general"``, ``context_id=None``) ->
    the EMAIL_SENT event is still recorded, with running_instance_id=NULL.
Every send gets a communication_events row and a real
``communication_event_id`` in the response, so ``provider_message_id`` is
always stored and inbound Resend webhooks (delivered/opened/bounced/
complained) can always correlate via record_inbound_status(), regardless
of which caller sent the email.
"""

import asyncio
import logging
from html import escape as html_escape
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.database.session import async_session_maker
from app.templates.services import TemplateService
from app.templates.exceptions import TemplateNotFoundError, TemplateValidationError
from app.integrations import IntegrationFactory, NativeProviderError
from app.jawis.client import get_jawis_client
from app.communication_events.schemas import CommunicationEventCreateSchema
from app.models.communication_event import CommunicationEventType, CommunicationEventChannel
from app.repositories.communication_event_repository import CommunicationEventRepository
from app.services.communication_event_service import CommunicationEventService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["Messages"])


async def _fetch_and_store_rfc822_message_id(event_id: str, provider_message_id: str) -> None:
    """Background task: fetch Resend's RFC822 Message-ID (GET /emails/{id})
    and store it on the already-created EMAIL_SENT CommunicationEvent.

    Runs AFTER the response has already been returned to the caller — this
    is what used to block the request (up to a 15s ceiling); moved out of
    the request-response path so JAWIS's 12s client timeout is never at
    risk from this specific call. Uses its own DB session (the request's
    session is gone by the time this runs, same pattern as
    CommunicationEventService._publish_to_jawis).

    Reply matching (record_email_reply's rfc822_message_id lookup) works
    exactly as before once this completes — a reply arriving in the brief
    window before it does simply won't match on this path yet; Gmail sync
    runs every 5 minutes, so this is not a practical race.
    """
    try:
        from app.providers import provider_registry, Channel
        email_provider = provider_registry.get_provider(Channel.EMAIL)
        if email_provider is None:
            return
        fetched = await email_provider._fetch_email(provider_message_id)
        rfc822_message_id = (fetched or {}).get("message_id")
    except Exception as exc:
        logger.warning(
            "Background rfc822_message_id fetch failed for provider_message_id=%s: %s "
            "— this message's replies won't be matchable via Message-ID/References "
            "(threadId-cache matching may still work if another message in the same "
            "thread succeeds)",
            provider_message_id, exc,
        )
        return

    if not rfc822_message_id:
        return

    async with async_session_maker() as db:
        try:
            repo = CommunicationEventRepository(db)
            event = await repo.get(UUID(event_id))
            if event is None:
                return
            payload = dict(event.payload or {})
            payload["rfc822_message_id"] = rfc822_message_id
            event.payload = payload
            await repo.update(event)
        except Exception as exc:
            logger.warning(
                "Could not store rfc822_message_id for communication_event_id=%s: %s",
                event_id, exc,
            )


def _plain_text_to_html(text: str) -> str:
    """Minimal HTML rendering of already-rendered plain-text content.

    Resend (and every other provider) implements open tracking by injecting
    a 1x1 tracking-pixel <img> into the HTML body — a text-only send has no
    HTML for a pixel to go into, so "opened" can never fire regardless of
    any tracking setting. This does not add templating capability (no new
    template field, TemplateService/TemplateRenderer untouched) — it only
    wraps the same rendered text so Resend has an HTML body to track.
    """
    return "<html><body>" + html_escape(text).replace("\n", "<br>\n") + "</body></html>"


class EmailSendRequest(BaseModel):
    lead_id: int
    # Optional: a manual custom email (no template) sends template_key=null
    # and supplies the final subject/body directly via variables.subject /
    # variables.body instead. When set, behavior is unchanged — the
    # template is fetched and rendered exactly as before.
    template_key: Optional[str] = None
    # Required: JAWIS supplies the lead's active stage at send time. JawCom
    # never looks this up itself (no get_lead_context()/CRM call) — it's
    # persisted into communication_events as-is and never mutated after
    # write, regardless of later webhook status changes.
    stage: str
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
    # ── 1. Validate request. template_key is optional — null means a
    #        manual custom email (no template); only validate/parse it
    #        when one was actually provided. ──────────────────────────
    template_uuid: Optional[UUID] = None
    if request.template_key is not None:
        try:
            template_uuid = UUID(request.template_key)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid template_key: {request.template_key!r}")

    # ── 2/3. Fetch lead via the lightweight JAWIS lead lookup (get_lead(),
    #        NOT get_lead_context() — manual sends need only name/email/
    #        phone, not stage/company/owner, and get_lead_context() requires
    #        stage_key, which this lightweight endpoint doesn't return) ──
    jawis_client = get_jawis_client()
    lead = await jawis_client.get_lead(str(request.lead_id))
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")

    recipient_name = lead.name
    recipient_email = lead.email
    if not recipient_email:
        raise HTTPException(status_code=400, detail=f"Lead {request.lead_id} has no email address on file")

    # ── 4/5. Fetch + render template via the existing TemplateService —
    #        OR, when template_key is null, treat this as a manual custom
    #        email: subject/body come directly from variables.subject /
    #        variables.body, used as-is (no template to look up, nothing
    #        to validate against a channel, no Jinja2 pass — this already
    #        *is* the final content, not a template containing it). ──────
    if template_uuid is not None:
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
    else:
        rendered = {
            "subject": request.variables.get("subject", ""),
            "content": request.variables.get("body", ""),
        }

    # ── 6. Send via the existing Resend integration (never JAWIS). The
    #        recipient was already resolved once in step 2/3 above — passed
    #        in directly so the integration performs no lead lookup of its
    #        own (no second JAWIS call). ──────────────────────────────────
    integration = IntegrationFactory.get("email_resend")
    try:
        result = await integration.execute({
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            "subject": rendered["subject"],
            "text": rendered["content"],
            "html": _plain_text_to_html(rendered["content"]),
        })
    except NativeProviderError as exc:
        logger.warning("Email send failed for lead=%s template=%s: %s", request.lead_id, request.template_key, exc)
        # Record the failure so it's visible in the lead's communication
        # history/timeline too, not just the HTTP response — previously a
        # send failure left no trace anywhere in communication_events.
        # No provider_message_id exists (Resend never accepted the send),
        # so there's nothing for a webhook to ever correlate against —
        # this row exists purely for visibility, not for later matching.
        failed_event_id: Optional[str] = None
        try:
            running_instance_id = str(UUID(request.context_id)) if request.context_id else None
            event_service = CommunicationEventService(db)
            failed_event = await event_service.create(
                CommunicationEventCreateSchema(
                    running_instance_id=running_instance_id,
                    lead_id=request.lead_id,
                    event_type=CommunicationEventType.FAILED.value,
                    channel=CommunicationEventChannel.EMAIL.value,
                    provider="resend",
                    provider_message_id=None,
                    payload={
                        "template_key": request.template_key,
                        "variables": request.variables,
                        "module": request.module,
                        "stage": request.stage,
                        "error": str(exc),
                        "source": "manual",
                        "status": "failed",
                    },
                )
            )
            failed_event_id = failed_event.id
        except (ValueError, IntegrityError) as log_exc:
            await db.rollback()
            logger.warning(
                "Could not record FAILED event for lead=%s context_id=%s: %s",
                request.lead_id, request.context_id, log_exc,
            )
        return EmailSendResponse(
            success=False,
            status="failed",
            provider_message_id=None,
            communication_event_id=failed_event_id,
            error=str(exc),
            provider="resend",
            provider_response={},
        )

    provider_message_id = result.get("provider_message_id")

    # ── 7. Record EMAIL_SENT for every send. Journey-originated sends
    #        (context_id set) get a real running_instance_id; manual/
    #        general sends (context_id=None) get running_instance_id=NULL —
    #        both are stored in communication_events (nullable FK, see
    #        migration b4c5d6e7f8a9) so webhooks can correlate delivered/
    #        opened/bounced/replied against either kind. The RFC822
    #        Message-ID (needed for Gmail reply matching) is NOT fetched
    #        here — Resend's POST response only returns their internal id;
    #        the RFC822 id is only available via a follow-up GET, which
    #        used to be awaited inline (up to a 15s ceiling) and is now a
    #        background task fired after this event exists, so the
    #        response returns immediately after the DB write. ────────────
    communication_event_id: Optional[str] = None
    try:
        running_instance_id = str(UUID(request.context_id)) if request.context_id else None
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
                    "stage": request.stage,
                    "rfc822_message_id": None,
                    "source": "manual",
                    "status": result.get("status", "sent"),
                },
            )
        )
        communication_event_id = event.id
        if provider_message_id:
            asyncio.create_task(
                _fetch_and_store_rfc822_message_id(event.id, provider_message_id)
            )
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
    # Required — see EmailSendRequest.stage above; same rule.
    stage: str
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

    # ── 2/3. Fetch lead via the lightweight JAWIS lead lookup (get_lead(),
    #        NOT get_lead_context() — manual sends need only name/email/
    #        phone, not stage/company/owner, and get_lead_context() requires
    #        stage_key, which this lightweight endpoint doesn't return) ──
    jawis_client = get_jawis_client()
    lead = await jawis_client.get_lead(str(request.lead_id))
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")

    recipient_name = lead.name
    recipient_phone = lead.phone
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

    # ── 6. Send via the existing Meta integration (never JAWIS). The
    #        recipient was already resolved once in step 2/3 above — passed
    #        in directly so the integration performs no lead lookup of its
    #        own (no second JAWIS call). ──────────────────────────────────
    integration = IntegrationFactory.get("whatsapp_meta")
    try:
        result = await integration.execute({
            "recipient_phone": recipient_phone,
            "recipient_name": recipient_name,
            "template_name": template.name,
            "variables": request.variables,
        })
    except NativeProviderError as exc:
        logger.warning("WhatsApp send failed for lead=%s template=%s: %s", request.lead_id, request.template_key, exc)
        # Mirrors the Email API's failure recording (added for parity — this
        # was previously silent, unlike the Email path).
        failed_event_id: Optional[str] = None
        try:
            running_instance_id = str(UUID(request.context_id)) if request.context_id else None
            event_service = CommunicationEventService(db)
            failed_event = await event_service.create(
                CommunicationEventCreateSchema(
                    running_instance_id=running_instance_id,
                    lead_id=request.lead_id,
                    event_type=CommunicationEventType.FAILED.value,
                    channel=CommunicationEventChannel.WHATSAPP.value,
                    provider="meta",
                    provider_message_id=None,
                    payload={
                        "template_key": request.template_key,
                        "variables": request.variables,
                        "module": request.module,
                        "stage": request.stage,
                        "error": str(exc),
                        "source": "manual",
                        "status": "failed",
                    },
                )
            )
            failed_event_id = failed_event.id
        except (ValueError, IntegrityError) as log_exc:
            await db.rollback()
            logger.warning(
                "Could not record FAILED event for lead=%s context_id=%s: %s",
                request.lead_id, request.context_id, log_exc,
            )
        return WhatsAppSendResponse(
            success=False,
            status="failed",
            provider_message_id=None,
            communication_event_id=failed_event_id,
        )

    provider_message_id = result.get("provider_message_id")

    # ── 7. Record WHATSAPP_SENT for every send (mirrors the Email API —
    #        previously gated on context_id being set, which meant manual/
    #        general WhatsApp sends were never recorded; fixed for parity).
    #        Journey-originated sends (context_id set) get a real
    #        running_instance_id; manual/general sends get NULL. ─────────
    communication_event_id: Optional[str] = None
    try:
        running_instance_id = str(UUID(request.context_id)) if request.context_id else None
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
                    "stage": request.stage,
                    "source": "manual",
                    "status": result.get("status", "sent"),
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
