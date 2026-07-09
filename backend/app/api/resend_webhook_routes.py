"""Inbound webhook handler for Resend email status updates.

Reuses the existing CommunicationEvent model — only that table is ever
written to here (via CommunicationEventService.record_inbound_status()).
No other table is touched, the execution engine is never invoked, JAWIS is
untouched, and app/providers/ (the provider abstraction) is unchanged.

Incoming events are matched to the original EMAIL_SENT event via
provider_message_id (Resend's email id), which is populated when a message
is sent through app/integrations/native_providers.py.

Note: Resend is an outbound-only transactional email API — it has no
concept of an inbound reply. There is no "email.replied" (or equivalent)
event in Resend's webhook catalog, so EMAIL_REPLIED can never be produced
from this endpoint; that would require a separate inbound-email channel
(e.g. IMAP/Gmail polling or Resend's own inbound-email feature, if/when
available), which is out of scope here — not built, not faked.

"email.delivery_delayed" is acknowledged (logged, 200 returned) but not
persisted as its own row — it's a transient in-flight status, not a
terminal outcome, and isn't one of the tracked CommunicationEventType
values.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.models.communication_event import CommunicationEventType, CommunicationEventChannel
from app.services.communication_event_service import CommunicationEventService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/resend", tags=["Webhooks"])

_EVENT_MAP = {
    "email.sent": CommunicationEventType.EMAIL_SENT.value,
    "email.delivered": CommunicationEventType.DELIVERED.value,
    "email.opened": CommunicationEventType.READ.value,
    "email.clicked": CommunicationEventType.CLICKED.value,
    "email.bounced": CommunicationEventType.BOUNCED.value,
    "email.complained": CommunicationEventType.COMPLAINED.value,
}

# Acknowledged but intentionally not persisted as their own row — see
# module docstring.
_ACKNOWLEDGED_ONLY = {"email.delivery_delayed"}


@router.post("")
async def receive_resend_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db_session),
):
    """Receive a single Resend webhook event.

    Only creates rows in communication_events. Every branch is logged so
    nothing is silently dropped, but webhook delivery must always get a 2xx
    for events we recognize (Resend retries indefinitely on non-2xx) —
    genuine processing failures are logged with full context and re-raised
    as a 500 so Resend retries the delivery instead of us losing it.
    """
    resend_type = payload.get("type")
    data = payload.get("data") or {}
    provider_message_id = data.get("email_id")

    if resend_type in _ACKNOWLEDGED_ONLY:
        logger.info(
            "Resend webhook: acknowledged non-persisted event type=%s provider_message_id=%s",
            resend_type, provider_message_id,
        )
        return {"received": True, "recorded": 0}

    event_type = _EVENT_MAP.get(resend_type)

    if not event_type:
        logger.warning(
            "Resend webhook: unrecognized event type=%s provider_message_id=%s — ignoring, "
            "no CommunicationEvent created. Full payload: %s",
            resend_type, provider_message_id, payload,
        )
        return {"received": True, "recorded": 0}

    if not provider_message_id:
        logger.warning(
            "Resend webhook: event type=%s has no data.email_id — cannot correlate to any "
            "communication_events row. Full payload: %s",
            resend_type, payload,
        )
        return {"received": True, "recorded": 0}

    service = CommunicationEventService(db)
    try:
        created = await service.record_inbound_status(
            provider_message_id=provider_message_id,
            event_type=event_type,
            channel=CommunicationEventChannel.EMAIL.value,
            provider="resend",
            payload={"raw_event": payload},
        )
    except Exception:
        logger.exception(
            "Resend webhook: failed to record event type=%s provider_message_id=%s — "
            "re-raising so Resend retries delivery instead of this event being lost",
            resend_type, provider_message_id,
        )
        raise

    if created is None:
        logger.info(
            "Resend webhook: type=%s provider_message_id=%s not recorded (no matching "
            "EMAIL_SENT anchor yet, or already recorded — idempotent no-op)",
            resend_type, provider_message_id,
        )

    return {"received": True, "recorded": 1 if created else 0}
