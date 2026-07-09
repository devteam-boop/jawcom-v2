"""Inbound webhook handler for Resend email status updates.

Reuses the existing CommunicationEvent model — only that table is ever
written to here (via CommunicationEventService.record_inbound_status()).
No other table is touched, the execution engine is never invoked, JAWIS is
untouched, and app/providers/ (the provider abstraction) is unchanged.

Incoming events are matched to the original EMAIL_SENT event via
provider_message_id (Resend's email id), which is populated when a message
is sent through app/integrations/native_providers.py.

Note: Resend is an outbound-only transactional email API — it has no
concept of an inbound reply. "email.clicked" is intentionally not mapped;
per scope, only delivered/read/failed are recorded for this provider
("replied" is not obtainable from Resend and is not faked here).
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
    "email.delivered": CommunicationEventType.DELIVERED.value,
    "email.opened": CommunicationEventType.READ.value,
    "email.bounced": CommunicationEventType.FAILED.value,
    "email.complained": CommunicationEventType.FAILED.value,
}


@router.post("")
async def receive_resend_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db_session),
):
    """Receive a single Resend webhook event.

    Only creates rows in communication_events; never raises on unmatched,
    duplicate, or unmapped ("email.sent"/"email.clicked") events — webhook
    delivery must always get a 200.
    """
    event_type = _EVENT_MAP.get(payload.get("type"))
    data = payload.get("data") or {}
    provider_message_id = data.get("email_id")

    if not event_type or not provider_message_id:
        return {"received": True, "recorded": 0}

    service = CommunicationEventService(db)
    created = await service.record_inbound_status(
        provider_message_id=provider_message_id,
        event_type=event_type,
        channel=CommunicationEventChannel.EMAIL.value,
        provider="resend",
        payload={"raw_event": payload},
    )

    return {"received": True, "recorded": 1 if created else 0}
