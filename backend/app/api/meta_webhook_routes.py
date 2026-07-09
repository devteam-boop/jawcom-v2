"""Inbound webhook handler for Meta WhatsApp Cloud API status/reply updates.

Reuses the existing CommunicationEvent model — only that table is ever
written to here (via CommunicationEventService.record_inbound_status()).
No other table is touched, the execution engine is never invoked, JAWIS is
untouched, and app/providers/ (the provider abstraction) is unchanged.

Incoming events are matched to the original WHATSAPP_SENT event via
provider_message_id (Meta's "wamid"), which is populated when a message is
sent through app/integrations/native_providers.py.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.dependencies import get_db_session
from app.models.communication_event import CommunicationEventType, CommunicationEventChannel
from app.services.communication_event_service import CommunicationEventService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/meta", tags=["Webhooks"])

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
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db_session),
):
    """Receive Meta's messages/statuses webhook payload.

    Only creates rows in communication_events; never raises on unmatched
    or duplicate events (webhook delivery must always get a 200, or the
    provider will retry indefinitely).
    """
    service = CommunicationEventService(db)
    recorded = 0

    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}

            # Outbound message status updates (delivered/read/failed).
            for status in value.get("statuses") or []:
                provider_message_id = status.get("id")
                event_type = _STATUS_MAP.get(status.get("status"))
                if not provider_message_id or not event_type:
                    continue
                created = await service.record_inbound_status(
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
                created = await service.record_inbound_status(
                    provider_message_id=provider_message_id,
                    event_type=CommunicationEventType.REPLIED.value,
                    channel=CommunicationEventChannel.WHATSAPP.value,
                    provider="meta",
                    dedup_key=message.get("id"),
                    payload={"raw_message": message},
                )
                if created:
                    recorded += 1

    return {"received": True, "recorded": recorded}
