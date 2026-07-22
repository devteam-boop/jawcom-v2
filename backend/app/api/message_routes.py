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
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
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
from app.services.email_idempotency_service import (
    check_and_reserve,
    compute_dedup_key,
    record_provider_message_id,
)
from app.whatsapp_templates.service import WhatsAppTemplateService

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


async def _send_email_and_record(
    event_id: UUID,
    request: "EmailSendRequest",
    recipient_email: str,
    recipient_name: Optional[str],
    rendered: Dict[str, str],
    dedup_key: str,
) -> None:
    """Background task: perform the actual Resend send and record the
    outcome, keyed on ``event_id`` already handed back to the caller in
    send_email()'s fast 202 response.

    ``dedup_key`` is the same idempotency key send_email() already reserved
    (app/services/email_idempotency_service.py) before dispatching this
    task — used only to backfill the real provider_message_id onto that
    reservation once Resend responds, so a retry that lands after this task
    finishes (but still within the 60s window) returns the real id on its
    IDEMPOTENCY_HIT instead of None.

    Lead lookup and template fetch/render already happened synchronously in
    send_email() (fast — one JAWIS callback + a local DB/Jinja2 pass, same
    as before this change, so a bad lead_id/template_key still gets an
    immediate 404/400). This task defers only the Resend API round-trip and
    the resulting DB write — the piece that actually blocked the response
    while JAWIS's client-side timeout was ticking. Uses its own DB session
    (the request's session is gone by the time this runs), same pattern as
    CommunicationEventService._publish_to_jawis and
    _fetch_and_store_rfc822_message_id above.

    Outcome is only ever visible via the resulting communication_event and
    its outbound JAWIS webhook (email_sent or failed) — JAWIS is expected
    to rely on that, not on this response, per Fix 1.
    """
    async with async_session_maker() as db:
        event_service = CommunicationEventService(db)
        running_instance_id = str(UUID(request.context_id)) if request.context_id else None
        settings = get_settings()
        sender_email = settings.RESEND_FROM_EMAIL or settings.EMAIL_SENDER

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
            logger.warning(
                "Email send failed for lead=%s template=%s: %s",
                request.lead_id, request.template_key, exc,
            )
            # Record the failure so it's visible in the lead's communication
            # history/timeline too, not just discarded — previously a send
            # failure left no trace anywhere in communication_events. No
            # provider_message_id exists (Resend never accepted the send),
            # so there's nothing for a webhook to ever correlate against —
            # this row exists purely for visibility, not for later matching.
            try:
                await event_service.create(
                    CommunicationEventCreateSchema(
                        id=str(event_id),
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
                            "subject": rendered["subject"],
                            "body": rendered["content"],
                            "from": sender_email,
                            "to": recipient_email,
                        },
                    )
                )
            except (ValueError, IntegrityError) as log_exc:
                await db.rollback()
                logger.warning(
                    "Could not record FAILED event for lead=%s context_id=%s event_id=%s: %s",
                    request.lead_id, request.context_id, event_id, log_exc,
                )
            return

        provider_message_id = result.get("provider_message_id")

        # Record EMAIL_SENT. Journey-originated sends (context_id set) get a
        # real running_instance_id; manual/general sends (context_id=None)
        # get running_instance_id=NULL — both are stored in
        # communication_events (nullable FK, see migration b4c5d6e7f8a9) so
        # webhooks can correlate delivered/opened/bounced/replied against
        # either kind. The RFC822 Message-ID (needed for Gmail reply
        # matching) is NOT fetched here — Resend's POST response only
        # returns their internal id; the RFC822 id is only available via a
        # follow-up GET, fired as its own background task below.
        try:
            event = await event_service.create(
                CommunicationEventCreateSchema(
                    id=str(event_id),
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
                        "subject": rendered["subject"],
                        "body": rendered["content"],
                        "from": sender_email,
                        "to": recipient_email,
                    },
                )
            )
            if provider_message_id:
                asyncio.create_task(
                    _fetch_and_store_rfc822_message_id(event.id, provider_message_id)
                )
                await record_provider_message_id(db, dedup_key, provider_message_id)
        except (ValueError, IntegrityError) as exc:
            await db.rollback()
            logger.warning(
                "Could not record EMAIL_SENT for lead=%s context_id=%s event_id=%s: %s",
                request.lead_id, request.context_id, event_id, exc,
            )


@router.post(
    "/email/send",
    response_model=EmailSendResponse,
    status_code=202,
    summary="Accept a production email send via the existing Resend integration (async)",
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
    #        stage_key, which this lightweight endpoint doesn't return).
    #        Stays synchronous — this is fast local-ish request validation,
    #        not the slow external round-trip JAWIS's timeout was hitting
    #        (see _send_email_and_record above), so bad input still gets an
    #        immediate 404/400 instead of a silent async failure. ────────
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
    #        *is* the final content, not a template containing it). Stays
    #        synchronous for the same reason as 2/3 above. ──────────────
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
        if template.status != "active":
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Template {request.template_key} is '{template.status}', not 'active' — "
                    "only active email templates can be sent"
                ),
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

    # ── 5.5. Idempotency (Manual Email only): a retried POST — same lead,
    #        template/key, stage, module, context_id, and rendered
    #        subject/body — within the last 60s must not trigger a second
    #        real Resend send. Computed from the RENDERED subject/body (the
    #        literal content Resend would receive), after template
    #        resolution above, so it's the same regardless of which branch
    #        (templated vs. manual custom email) produced `rendered`. See
    #        app/services/email_idempotency_service.py for the atomic
    #        reserve-or-detect-duplicate logic and IDEMPOTENCY_HIT/MISS
    #        logging. ───────────────────────────────────────────────────
    dedup_key = compute_dedup_key(
        lead_id=request.lead_id,
        template_key=request.template_key,
        stage=request.stage,
        module=request.module,
        context_id=request.context_id,
        subject=rendered["subject"],
        body=rendered["content"],
    )
    # Per-attempt id (distinct from communication_event_id, which stays the
    # same across the original request and every one of its duplicates) —
    # logging-only, lets IDEMPOTENCY_HIT/MISS/EXPIRED lines be traced back
    # to one specific HTTP request. Never included in the response.
    request_id = str(uuid4())
    idempotency = await check_and_reserve(
        db, dedup_key,
        lead_id=request.lead_id, template_key=request.template_key, request_id=request_id,
    )
    if idempotency.is_duplicate:
        # Same response shape as a first-time send (Fix 1 below) — no
        # Resend call, no new communication_events row; just the already-
        # reserved ids from the original request. If the original send
        # hasn't reached Resend yet (provider_message_id still None), say
        # so explicitly ("processing") rather than implying delivery is
        # already complete — "queued" once a real provider_message_id is
        # known matches the original request's own eventual outcome.
        return EmailSendResponse(
            success=True,
            status="processing" if idempotency.provider_message_id is None else "queued",
            provider_message_id=idempotency.provider_message_id,
            communication_event_id=str(idempotency.communication_event_id),
        )

    # ── 6/7. Fast-ack (Fix 1): hand back a stable, pre-generated event_id
    #        immediately and defer the actual Resend call + resulting DB
    #        write to a background task — see _send_email_and_record above.
    #        JAWIS is expected to rely on the outbound webhook
    #        (email_sent/failed) for the real outcome, not this response.
    #        NOTE: this does not eliminate a Render free-tier cold-start
    #        spin-up ahead of this handler (that's platform-level, before
    #        any application code runs) — it only removes this handler's
    #        own contribution (the Resend round-trip) from the request's
    #        total latency. See report for the keep-warm/paid-tier
    #        recommendation, which is the actual fix for cold start itself.
    event_id = idempotency.communication_event_id
    asyncio.create_task(
        _send_email_and_record(event_id, request, recipient_email, recipient_name, rendered, dedup_key)
    )

    # ── 8. Return fast. `success`/`status` now mean "accepted for
    #        processing", not "delivered" — delivery outcome follows via
    #        the communication_event + webhook created in the background
    #        task above. ─────────────────────────────────────────────────
    return EmailSendResponse(
        success=True,
        status="queued",
        provider_message_id=None,
        communication_event_id=str(event_id),
    )


class WhatsAppSendRequest(BaseModel):
    lead_id: int
    # Legacy path — a JawCom Template row's id (generic templates table).
    # Optional now (was required) so existing callers are unaffected while
    # template_name (below) becomes an alternative way to address a
    # Meta-synced template (WhatsApp Template Management Phase 1, Feature 5).
    # Exactly one of template_key/template_name must be supplied.
    template_key: Optional[str] = None
    # New path — a Meta WhatsApp template's own name (whatsapp_templates
    # table, populated only by Meta Sync — see app/whatsapp_templates/).
    # Takes precedence over template_key when both are given.
    template_name: Optional[str] = None
    language: str = "en_US"
    # Freeform (non-template) send — WhatsApp 24h Session Window feature.
    # Exactly one of template_name/template_key OR body must be supplied.
    # Only Meta-acceptable while this lead's 24h customer-service window is
    # open (see is_whatsapp_session_window_active() below); the Inbox
    # composer only offers this path once it has computed the same window
    # as active client-side, but this is still re-checked server-side.
    body: Optional[str] = None
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


async def _send_whatsapp_and_record(
    event_id: UUID,
    request: "WhatsAppSendRequest",
    recipient_phone: str,
    recipient_name: Optional[str],
    resolved_template_name: Optional[str],
    language: str,
    rendered_body: str,
) -> None:
    """Background task: perform the actual Meta send and record the
    outcome — mirrors _send_email_and_record above; see send_whatsapp()
    for what stays synchronous vs. deferred here.

    ``resolved_template_name``/``language`` are what Meta actually sends
    against, regardless of whether the caller addressed the template via
    the new template_name path or the legacy template_key path (WhatsApp
    Template Management Phase 1, Feature 5) — always stored verbatim in the
    resulting communication_event's payload (Feature 7: "Store
    template_name in communication_events. Do not infer later.").

    ``resolved_template_name is None`` means a freeform (24h session
    window) send instead — MetaWhatsAppIntegration.execute() branches on
    the presence of "text" vs "template_name" in the payload below and
    calls MetaProvider.send_message() (plain-text Graph API) rather than
    send_template_message().
    """
    async with async_session_maker() as db:
        event_service = CommunicationEventService(db)
        running_instance_id = str(UUID(request.context_id)) if request.context_id else None
        settings = get_settings()
        # Meta's Graph API only exposes an opaque phone_number_id here (see
        # app/providers/meta/meta_provider.py) — there is no separate
        # human-readable "display phone number" setting in this codebase,
        # so that id is the best available sender identity for display.
        sender = settings.WHATSAPP_PHONE_NUMBER_ID

        integration = IntegrationFactory.get("whatsapp_meta")
        try:
            result = await integration.execute({
                "recipient_phone": recipient_phone,
                "recipient_name": recipient_name,
                "template_name": resolved_template_name,
                "language": language,
                "variables": request.variables,
                "text": rendered_body if resolved_template_name is None else None,
            })
        except NativeProviderError as exc:
            logger.warning(
                "WhatsApp send failed for lead=%s template=%s: %s",
                request.lead_id, resolved_template_name, exc,
            )
            try:
                await event_service.create(
                    CommunicationEventCreateSchema(
                        id=str(event_id),
                        running_instance_id=running_instance_id,
                        lead_id=request.lead_id,
                        event_type=CommunicationEventType.FAILED.value,
                        channel=CommunicationEventChannel.WHATSAPP.value,
                        provider="meta",
                        provider_message_id=None,
                        payload={
                            "template_key": request.template_key,
                            "template_name": resolved_template_name,
                            "language": language,
                            "variables": request.variables,
                            "module": request.module,
                            "stage": request.stage,
                            "error": str(exc),
                            "source": "manual",
                            "status": "failed",
                            "body": rendered_body,
                            "from": sender,
                            "to": recipient_phone,
                        },
                    )
                )
            except (ValueError, IntegrityError) as log_exc:
                await db.rollback()
                logger.warning(
                    "Could not record FAILED event for lead=%s context_id=%s event_id=%s: %s",
                    request.lead_id, request.context_id, event_id, log_exc,
                )
            return

        provider_message_id = result.get("provider_message_id")

        try:
            await event_service.create(
                CommunicationEventCreateSchema(
                    id=str(event_id),
                    running_instance_id=running_instance_id,
                    lead_id=request.lead_id,
                    event_type=CommunicationEventType.WHATSAPP_SENT.value,
                    channel=CommunicationEventChannel.WHATSAPP.value,
                    provider="meta",
                    provider_message_id=provider_message_id,
                    payload={
                        "template_key": request.template_key,
                        "template_name": resolved_template_name,
                        "language": language,
                        "variables": request.variables,
                        "module": request.module,
                        "stage": request.stage,
                        "source": "manual",
                        "status": result.get("status", "sent"),
                        "body": rendered_body,
                        "from": sender,
                        "to": recipient_phone,
                    },
                )
            )
        except (ValueError, IntegrityError) as exc:
            await db.rollback()
            logger.warning(
                "Could not record WHATSAPP_SENT for lead=%s context_id=%s event_id=%s: %s",
                request.lead_id, request.context_id, event_id, exc,
            )


@router.post(
    "/whatsapp/send",
    response_model=WhatsAppSendResponse,
    status_code=202,
    summary="Accept a production WhatsApp message send via the existing Meta integration (async)",
)
async def send_whatsapp(
    request: WhatsAppSendRequest,
    db: AsyncSession = Depends(get_db_session),
):
    # ── 1. Validate request. Exactly one of template_name (new — Meta-synced
    #        whatsapp_templates, Phase 1 Feature 5) / template_key (legacy —
    #        generic templates table) — an approved-template send — OR body
    #        — a freeform reply, WhatsApp 24h Session Window feature, only
    #        Meta-acceptable inside the lead's 24h customer-service window —
    #        must be supplied. template_name wins if both template fields
    #        are given. ─────────────────────────────────────────────────────
    has_template = bool(request.template_name or request.template_key)
    if has_template and request.body:
        raise HTTPException(status_code=400, detail="Provide either a template (template_name/template_key) or body, not both")
    if not has_template and not request.body:
        raise HTTPException(status_code=400, detail="One of template_name, template_key, or body is required")

    template_uuid: Optional[UUID] = None
    if not request.template_name and request.template_key:
        try:
            template_uuid = UUID(request.template_key)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid template_key: {request.template_key!r}")

    # ── 2/3. Fetch lead via the lightweight JAWIS lead lookup (get_lead(),
    #        NOT get_lead_context() — manual sends need only name/email/
    #        phone, not stage/company/owner, and get_lead_context() requires
    #        stage_key, which this lightweight endpoint doesn't return).
    #        Stays synchronous — see send_email()'s equivalent comment. ──
    jawis_client = get_jawis_client()
    lead = await jawis_client.get_lead(str(request.lead_id))
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")

    recipient_name = lead.name
    recipient_phone = lead.phone
    if not recipient_phone:
        raise HTTPException(status_code=400, detail=f"Lead {request.lead_id} has no phone number on file")

    # ── 4/5. Resolve the template — OR, for a freeform reply, re-verify the
    #        24h session window server-side (belt-and-suspenders: the Inbox
    #        composer already only offers this path once its own client-side
    #        computation over the same communication_events says the window
    #        is open; Meta's Graph API would also reject an out-of-window
    #        freeform send, but checking here gives a clear 400 instead of
    #        surfacing Meta's error text). Stays synchronous — local DB
    #        lookup, not the external Meta round-trip being deferred below.
    if request.body:
        event_service_check = CommunicationEventService(db)
        if not await event_service_check.is_whatsapp_session_window_active(request.lead_id):
            raise HTTPException(
                status_code=400,
                detail=(
                    "The WhatsApp customer service session has expired. "
                    "Send an approved template to reopen the conversation."
                ),
            )
        resolved_template_name = None
        rendered_body = request.body
    elif request.template_name:
        # New path: Meta-synced whatsapp_templates (WhatsApp Template
        # Management Phase 5). Resolves to the LATEST version of this
        # (name, language) whose status is APPROVED — never a Pending/
        # Rejected/Draft/Disabled/Paused version even if it's the newest
        # one, and never silently falls back to some other version: if no
        # approved version exists at all, the send fails clearly here with
        # an explicit error rather than picking anything else.
        wa_service = WhatsAppTemplateService(db)
        wa_template = await wa_service.resolve_latest_approved_by_name(request.template_name, request.language)
        if wa_template is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No APPROVED version of WhatsApp template '{request.template_name}' ({request.language}) "
                    "exists — either it has never been approved by Meta, or only Pending/Rejected/Draft "
                    "versions exist. Run a Meta sync if you believe this is stale."
                ),
            )
        resolved_template_name = wa_template.template_name
        rendered_body = (await wa_service.preview(UUID(wa_template.id), request.variables)).body
    else:
        # Legacy path — unchanged behavior.
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
            # Reuses the same TemplateRenderer instance TemplateService
            # already owns (mirrors render_email() above) — rendering logic
            # itself is not duplicated. The rendered body isn't sent
            # directly: Meta's WhatsApp Business API only accepts approved
            # templates addressed by name with positional parameters (see
            # below), the same contract SendWhatsAppExecutor already uses —
            # this call exists to validate the variables against the
            # template before sending. The rendered text is still kept (not
            # discarded) as the best available display body for the
            # timeline/webhook (Fix 4) even though Meta itself renders the
            # approved template server-side.
            rendered_body = template_service.renderer.render_whatsapp(template.content, request.variables)
        except TemplateValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        resolved_template_name = template.name

    # ── 6/7. Fast-ack (Fix 1): defer the actual Meta call + resulting DB
    #        write to a background task — see _send_whatsapp_and_record
    #        above and send_email()'s equivalent comment for the full
    #        rationale (including the cold-start caveat). ───────────────
    event_id = uuid4()
    asyncio.create_task(
        _send_whatsapp_and_record(
            event_id, request, recipient_phone, recipient_name,
            resolved_template_name, request.language, rendered_body,
        )
    )

    # ── 8. Return fast — see send_email()'s equivalent comment on what
    #        success/status now mean. ───────────────────────────────────
    return WhatsAppSendResponse(
        success=True,
        status="queued",
        provider_message_id=None,
        communication_event_id=str(event_id),
    )


class JawisTemplateSchema(BaseModel):
    id: str
    key: str  # same value as id — templates.template_key elsewhere in this API IS the template's id
    name: str
    channel: str
    status: str
    subject: Optional[str] = None
    body: str
    variables: List[str] = Field(default_factory=list)
    # WhatsApp Template Management additions — populated only for
    # channel=whatsapp entries (Meta-synced whatsapp_templates), None/absent
    # for every other channel. template_name duplicates `name` under the
    # literal field name JAWIS's WhatsApp picker expects; `name` is kept
    # unchanged for whatever already parses it on other channels.
    template_name: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None


@router.get(
    "/templates",
    response_model=List[JawisTemplateSchema],
    summary="List templates for JAWIS's template picker (read-only, reuses the Template Engine)",
)
async def list_templates_for_jawis(
    channel: Optional[str] = None,
    status: Optional[str] = None,
    language: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Thin read wrapper around the existing Template Engine
    (app/templates/services.py TemplateService), mounted under /api/messages
    (not /api/templates) deliberately: /api/templates already exists as
    JawCom's own unauthenticated CRUD API used by the frontend template
    editor (see app/api/template_routes.py, frontend/src/services/
    templates.js) — Bearer-protecting that path or reusing it here would
    either break the frontend or require duplicating the CRUD router.
    Mounting under /api/messages instead means this endpoint automatically
    inherits the existing Bearer JAWCOM_API_TOKEN protection already applied
    to that whole prefix (see app/core/jawis_auth_middleware.py) with no
    middleware change needed.

    channel=whatsapp returns only Meta-synced, APPROVED whatsapp_templates
    rows (TemplateService.list_templates() special-cases this — see
    app/templates/services.py) — this is JAWIS's only path to WhatsApp
    templates; JAWIS never calls Meta directly. No template storage or
    variable-extraction logic is duplicated here: `t.variables` is already
    correctly populated by TemplateService for both generic (name-keyed) and
    WhatsApp (Meta's positional {{1}}/{{2}}, order-sensitive) templates.

    Email Template Lifecycle: email-channel rows are always filtered down to
    status="active" here, regardless of the `status` query param passed in
    (or its absence) — a draft or archived email template must never reach
    JAWIS's template picker (fetch endpoint or manual-send picker; both are
    this same endpoint). Every other channel's filtering is unchanged.
    """
    template_service = TemplateService(db)
    templates = await template_service.list_templates(channel=channel, status=status, language=language)
    templates = [t for t in templates if not (t.channel == "email" and t.status != "active")]
    return [
        JawisTemplateSchema(
            id=t.id,
            key=t.id,
            name=t.name,
            channel=t.channel,
            status=t.status,
            subject=t.subject,
            body=t.content,
            variables=t.variables,
            template_name=t.name if t.channel == "whatsapp" else None,
            language=t.language,
            category=t.category,
        )
        for t in templates
    ]
