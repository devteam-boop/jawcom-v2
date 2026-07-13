"""Inbound webhook handler for Meta WhatsApp Cloud API status/reply/template
updates.

Two independent kinds of change ride the same Meta webhook delivery:
  - message status/reply updates -> CommunicationEvent (unchanged, see below)
  - message_template_status_update -> whatsapp_templates (WhatsApp Template
    Management Part 3), added here rather than as a second receiver per
    that feature's explicit instruction to share this endpoint instead of
    duplicating a GET-verify/POST-signature receiver.

Message status/reply handling reuses the existing CommunicationEvent model
— only that table is ever written to for those events (via
CommunicationEventService.record_inbound_status()). Template status updates
only ever write to whatsapp_templates, via WhatsAppTemplateService.
update_status_from_webhook(). Neither path touches the execution engine,
JAWIS, or app/providers/ (the provider abstraction).

Incoming message status/reply events are matched to the original
WHATSAPP_SENT event via provider_message_id (Meta's "wamid"), which is
populated when a message is sent through app/integrations/native_providers.py.
Template status events are matched via message_template_id, JawCom's
provider_template_id.

Every POST delivery's raw body is verified against X-Hub-Signature-256
(HMAC-SHA256 keyed with META_APP_SECRET) before any of it is parsed or
trusted — this must happen first, ahead of both branches above.
"""

import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.dependencies import get_db_session
from app.models.communication_event import CommunicationEventType, CommunicationEventChannel
from app.services.communication_event_service import CommunicationEventService
from app.whatsapp_templates.service import WhatsAppTemplateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/meta", tags=["Webhooks"])


def _verify_signature(raw_body: bytes, signature_header: Optional[str], app_secret: Optional[str]) -> bool:
    """Verify Meta's X-Hub-Signature-256 header (``sha256=<hex hmac>``)
    against the raw request body, keyed with META_APP_SECRET.

    Constant-time comparison (hmac.compare_digest) to avoid a timing side
    channel. Returns False (never raises) on any missing/malformed input so
    the caller can uniformly reject with a single 403.
    """
    if not app_secret or not signature_header:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    provided = signature_header[len("sha256="):]
    return hmac.compare_digest(expected, provided)

# Meta's real "statuses[].status" values. "sent" maps to WHATSAPP_SENT —
# our own send already creates this row synchronously, so Meta's webhook
# copy of it is almost always an idempotent no-op (same pattern as
# Resend's "email.sent", see resend_webhook_routes.py); harmless self-heal
# if the synchronous insert ever failed while the send still went through.
_STATUS_MAP = {
    "sent": CommunicationEventType.WHATSAPP_SENT.value,
    "delivered": CommunicationEventType.DELIVERED.value,
    "read": CommunicationEventType.READ.value,
    "failed": CommunicationEventType.FAILED.value,
}


@router.get("/", include_in_schema=False)
async def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta's one-time webhook registration handshake (GET with hub.* query params)."""
    settings = get_settings()
    expected = settings.META_WEBHOOK_VERIFY_TOKEN
    if not expected:
        logger.warning("META_WEBHOOK_VERIFY_TOKEN not configured — rejecting verification handshake")
        raise HTTPException(status_code=403, detail="Webhook verify token not configured")
    if hub_mode == "subscribe" and hub_verify_token == expected:
        return PlainTextResponse(hub_challenge or "")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/")
async def receive_meta_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Receive Meta's messages/statuses/message_template_status_update
    webhook payload.

    The raw body is read and its signature verified BEFORE anything is
    parsed or trusted — a request with a missing/invalid
    X-Hub-Signature-256 is rejected with 403 and never reaches either
    branch below, regardless of what it claims to contain.

    Never raises on unmatched or duplicate events past that point (webhook
    delivery must always get a 200, or the provider will retry
    indefinitely) — matching the existing message-status handling below.
    """
    raw_body = await request.body()
    settings = get_settings()
    if not _verify_signature(raw_body, request.headers.get("X-Hub-Signature-256"), settings.META_APP_SECRET):
        logger.warning("Meta webhook POST rejected: missing/invalid X-Hub-Signature-256")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event_service = CommunicationEventService(db)
    template_service = WhatsAppTemplateService(db)
    recorded = 0
    templates_updated = 0

    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}

            # Template approval/rejection pushes (WhatsApp Template
            # Management Part 3) — Meta delivers these with
            # change["field"] == "message_template_status_update", sharing
            # this same endpoint/entry structure rather than a separate one.
            if change.get("field") == "message_template_status_update":
                meta_template_id = value.get("message_template_id")
                if meta_template_id is None:
                    logger.warning("message_template_status_update with no message_template_id, skipping: %s", value)
                    continue
                new_status = value.get("event") or value.get("status")
                reason = value.get("reason")
                if reason == "NONE":  # Meta's literal placeholder when not rejected
                    reason = None
                updated = await template_service.update_status_from_webhook(
                    meta_template_id=str(meta_template_id),
                    status=new_status,
                    rejection_reason=reason,
                    language=value.get("message_template_language"),
                )
                if updated is None:
                    logger.info(
                        "message_template_status_update for unknown meta_template_id=%s "
                        "(not yet synced/created locally) — skipped",
                        meta_template_id,
                    )
                else:
                    templates_updated += 1
                continue

            # Outbound message status updates (delivered/read/failed).
            for status in value.get("statuses") or []:
                provider_message_id = status.get("id")
                event_type = _STATUS_MAP.get(status.get("status"))
                if not provider_message_id or not event_type:
                    continue
                created = await event_service.record_inbound_status(
                    provider_message_id=provider_message_id,
                    event_type=event_type,
                    channel=CommunicationEventChannel.WHATSAPP.value,
                    provider="meta",
                    payload={"raw_status": status},
                )
                if created:
                    recorded += 1

            # Inbound customer replies. Matched via context.id (the message
            # this is a reply to) — if Meta didn't include it, there is no
            # provider_message_id to match against, so it is skipped.
            #
            # dedup_key=message["id"] (WhatsApp's own message id, distinct
            # per inbound message): a lead can send multiple genuine
            # separate replies to the same outbound message, all sharing
            # the same context.id — without this, only the first reply
            # would ever be recorded (provider_message_id+event_type
            # idempotency would silently treat every later reply as a
            # duplicate of the first).
            for message in value.get("messages") or []:
                context = message.get("context") or {}
                provider_message_id = context.get("id")
                if not provider_message_id:
                    logger.info(
                        "Inbound WhatsApp message has no context.id — cannot match "
                        "to a sent message via provider_message_id, skipping"
                    )
                    continue
                created = await event_service.record_inbound_status(
                    provider_message_id=provider_message_id,
                    event_type=CommunicationEventType.REPLIED.value,
                    channel=CommunicationEventChannel.WHATSAPP.value,
                    provider="meta",
                    dedup_key=message.get("id"),
                    payload={"raw_message": message},
                )
                if created:
                    recorded += 1

    return {"received": True, "recorded": recorded, "templates_updated": templates_updated}
