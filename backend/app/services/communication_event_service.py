import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_events.schemas import (
    CommunicationEventCreateSchema,
    CommunicationEventSchema,
)
from app.config.settings import get_settings
from app.database.session import async_session_maker
from app.models.communication_event import CommunicationEvent
from app.repositories.communication_event_repository import CommunicationEventRepository

logger = logging.getLogger(__name__)

# Event types that must be published to JAWIS (Decision 5) — "opened" (email)
# and "read" (WhatsApp) are the same stored event_type ("read"), so a single
# entry covers both without extra mapping. Deliberately excludes
# bounced/complained/journey_started/etc. — not in the spec's listed set.
_JAWIS_WEBHOOK_EVENT_TYPES = {
    "email_sent", "whatsapp_sent", "delivered", "read", "clicked", "replied", "failed",
}

# JAWIS's webhook only accepts its own dotted "message.*" names for the
# WhatsApp channel; our stored event_type values (whatsapp_sent, delivered,
# read, failed, replied — see CommunicationEventType) were being sent
# verbatim and rejected with 422. Email's stored names (email_sent,
# delivered, read, ...) are already what JAWIS accepts for the email
# channel, so this mapping is applied ONLY when channel=="whatsapp" —
# email's outbound payload is completely unchanged.
_WHATSAPP_JAWIS_EVENT_NAMES = {
    "whatsapp_sent": "message.sent",
    "delivered": "message.delivered",
    "read": "message.read",
    "clicked": "message.clicked",
    "failed": "message.failed",
    "replied": "message.reply",
}
_JAWIS_WEBHOOK_RETRY_DELAYS = [1, 5, 15]  # seconds; 1 initial attempt + 3 retries

# Recency window for the phone-number reply-matching fallback (Issue 2) —
# how far back to look for a prior whatsapp_sent to the same number when
# Meta's inbound message has no context.id. Deliberately generous (72h)
# since a customer replying to yesterday's message is still a genuine,
# matchable reply, not a random inbound.
_REPLY_PHONE_MATCH_WINDOW_HOURS = 72

# WhatsApp's own 24h customer-service session window (Meta policy, not a
# JawCom setting) — freeform (non-template) sends are only Meta-acceptable
# within 24h of the customer's last inbound message. Mirrors the same
# window the Inbox computes client-side from the same 'replied' events
# (frontend/src/modules/inbox/whatsappWindow.js) — kept in sync manually
# since both derive from the same rule, not from a shared constant module.
WHATSAPP_SESSION_WINDOW_HOURS = 24


async def _publish_to_jawis(schema: CommunicationEventSchema) -> bool:
    """Fire-and-forget POST of one communication_events row to JAWIS_WEBHOOK_URL.

    Sole JawCom->JAWIS sync mechanism (Decision 5) — JAWIS pulls nothing.
    No existing outbound-HTTP-retry infrastructure exists elsewhere in this
    codebase (retry_service.py's retry_delays are for re-executing a failed
    Journey node, a different concern) — this is new, minimal, in-process
    retry/backoff, not a durable queue (would require a new dependency).
    Runs via asyncio.create_task() so it never blocks the response to
    whatever created the event (a Resend/Meta webhook, a manual send, a
    Gmail reply) — those must always get a fast response regardless of
    JAWIS's availability.

    Also reused directly (awaited, not detached) by
    scripts/backfill_jawis_sync.py to re-publish rows where
    jawis_synced_at IS NULL — same payload builder, same retry/backoff, no
    separate serialization to drift out of sync. Returns True on a
    confirmed 2xx (jawis_synced_at has been set), False otherwise.
    """
    settings = get_settings()
    url = settings.JAWIS_WEBHOOK_URL
    if not url:
        logger.warning(
            "JAWIS_WEBHOOK_URL not configured — skipping webhook publish for "
            "event_id=%s event_type=%s (event remains in communication_events; "
            "jawis_synced_at stays NULL)",
            schema.id, schema.event_type,
        )
        return False

    payload = schema.payload or {}
    # Outbound name only — communication_events.event_type in the DB is
    # never touched, only what's put on the wire to JAWIS here.
    jawis_event_type = schema.event_type
    if schema.channel == "whatsapp":
        jawis_event_type = _WHATSAPP_JAWIS_EVENT_NAMES.get(schema.event_type, schema.event_type)
    body = {
        # Stable per-event identifier for JAWIS-side dedupe on retry.
        "event_id": schema.id,
        "lead_id": schema.lead_id,
        "event_type": jawis_event_type,
        "channel": schema.channel,
        "provider": schema.provider,
        "provider_message_id": schema.provider_message_id,
        "journey_id": schema.journey_id,
        "node_id": schema.node_id,
        # Immutable snapshot from send time. Journey-driven sends
        # (send_whatsapp_executor.py / send_email_executor.py) write
        # "stage_at_send"; manual sends (app/api/message_routes.py) still
        # write the pre-existing "stage" key — both are set once, at send
        # time, and never re-derived, so falling back to "stage" preserves
        # the manual-send contract unchanged.
        "stage": payload.get("stage_at_send", payload.get("stage")),
        "source": payload.get("source"),
        "status": payload.get("status"),
        "template_key": payload.get("template_key"),
        # Display fields for JAWIS's timeline cards — always at this
        # top-level path regardless of event_type, so JAWIS never has to
        # dig into a nested raw_event/raw_status/raw_message differently
        # per event type. Populated at write time: for *_sent/failed by the
        # send endpoint (app/api/message_routes.py), for delivered/read/
        # clicked/replied/bounced/complained by forwarding from the
        # original *_sent event's payload (see record_inbound_status /
        # record_email_reply below) — never re-derived here.
        "subject": payload.get("subject"),
        "body": payload.get("body"),
        "from": payload.get("from"),
        "to": payload.get("to"),
        "occurred_at": schema.occurred_at.isoformat() if schema.occurred_at else None,
        "payload": payload,
    }
    headers = {"Authorization": f"Bearer {settings.JAWCOM_API_TOKEN}"} if settings.JAWCOM_API_TOKEN else {}

    for attempt, delay in enumerate([0, *_JAWIS_WEBHOOK_RETRY_DELAYS]):
        if delay:
            await asyncio.sleep(delay)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=body, headers=headers)

            # TEMP DIAGNOSTICS ONLY — no effect on control flow, retries, or
            # any other behavior below. Fires purely to capture why JAWIS
            # rejected the payload as unprocessable.
            if response.status_code == 422:
                redacted_headers = {
                    k: ("Bearer ***redacted***" if k.lower() == "authorization" else v)
                    for k, v in headers.items()
                }
                try:
                    parsed_response_json = response.json()
                except ValueError:
                    parsed_response_json = None
                logger.error(
                    "JAWIS webhook 422 Unprocessable Entity — full diagnostic dump for event_id=%s "
                    "event_type=%s\n"
                    "  URL: %s\n"
                    "  Headers sent: %s\n"
                    "  Complete JSON payload sent: %s\n"
                    "  HTTP status: %s\n"
                    "  Full response body (raw): %s\n"
                    "  Parsed JSON response: %s",
                    schema.id, schema.event_type, url, redacted_headers,
                    json.dumps(body, default=str), response.status_code,
                    response.text, json.dumps(parsed_response_json, default=str) if parsed_response_json is not None else None,
                )

            if response.status_code < 400:
                async with async_session_maker() as session:
                    await CommunicationEventRepository(session).mark_jawis_synced(
                        UUID(schema.id), datetime.utcnow(),
                    )
                return True
            logger.warning(
                "JAWIS webhook publish failed (attempt %s/%s): HTTP %s for event_id=%s event_type=%s",
                attempt + 1, len(_JAWIS_WEBHOOK_RETRY_DELAYS) + 1, response.status_code, schema.id, schema.event_type,
            )
        except httpx.RequestError as exc:
            logger.warning(
                "JAWIS webhook publish failed (attempt %s/%s): %s for event_id=%s event_type=%s",
                attempt + 1, len(_JAWIS_WEBHOOK_RETRY_DELAYS) + 1, exc, schema.id, schema.event_type,
            )

    logger.error(
        "JAWIS webhook publish exhausted all retries for event_id=%s event_type=%s — event is NOT lost "
        "locally (already committed to communication_events), only JAWIS's copy is missing until a manual resync",
        schema.id, schema.event_type,
    )
    return False


class CommunicationEventService:
    def __init__(self, session: AsyncSession):
        self.repo = CommunicationEventRepository(session)

    async def create(self, data: CommunicationEventCreateSchema) -> CommunicationEventSchema:
        # "source": manual | automation. Explicit callers (message_routes.py,
        # the Communication Engine's public send APIs) always set it
        # themselves. Callers that don't set it (Journey Engine's
        # ExecutionEngine._record_communication_event(), untouched per
        # scope) default to "automation" here — this tags every event
        # without requiring any change to Execution Engine.
        payload = dict(data.payload or {})
        payload.setdefault("source", "automation")
        payload.setdefault("status", data.event_type)

        event = CommunicationEvent(
            id=UUID(data.id) if data.id else uuid4(),
            running_instance_id=UUID(data.running_instance_id) if data.running_instance_id else None,
            journey_id=UUID(data.journey_id) if data.journey_id else None,
            lead_id=data.lead_id,
            node_id=data.node_id,
            event_type=data.event_type,
            channel=data.channel,
            provider=data.provider,
            provider_message_id=data.provider_message_id,
            payload=payload,
        )
        created = await self.repo.create(event)
        schema = self._to_schema(created)

        if schema.event_type in _JAWIS_WEBHOOK_EVENT_TYPES:
            asyncio.create_task(_publish_to_jawis(schema))

        return schema

    async def get(self, event_id: UUID) -> CommunicationEventSchema:
        event = await self.repo.get(event_id)
        if not event:
            raise ValueError(f"CommunicationEvent {event_id} not found")
        return self._to_schema(event)

    async def list(
        self, skip: int = 0, limit: int = 100,
        running_instance_id: Optional[UUID] = None,
        journey_id: Optional[UUID] = None,
        lead_id: Optional[int] = None,
        event_type: Optional[str] = None,
        provider_message_id: Optional[str] = None,
        channel: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[CommunicationEventSchema]:
        events = await self.repo.get_all(
            skip=skip, limit=limit,
            running_instance_id=running_instance_id,
            journey_id=journey_id,
            lead_id=lead_id,
            event_type=event_type,
            provider_message_id=provider_message_id,
            channel=channel,
            source=source,
        )
        return [self._to_schema(e) for e in events]

    async def resolve_whatsapp_reply_anchor(
        self, context_id: Optional[str], from_phone: Optional[str],
    ) -> Tuple[Optional[str], str]:
        """Issue 2 — decide which prior whatsapp_sent event (by
        provider_message_id) an inbound WhatsApp message should be
        attached to, and by which strategy, so a genuine reply is never
        silently dropped just because Meta didn't send a context.id (a
        "fresh" message rather than a formal swipe-to-reply has none).

        Tries, in order:
          1. context.id, if present — the primary path (Meta explicitly
             told us which outbound message this replies to). If Meta gave
             us a context.id that doesn't match anything we actually sent,
             falls through to the phone strategies below rather than
             giving up.
          2. The most recent whatsapp_sent to this phone number within the
             last _REPLY_PHONE_MATCH_WINDOW_HOURS — a fresh message from a
             known number is still a genuine reply in an ongoing
             conversation.
          3. The most recent whatsapp_sent to this phone number ever
             (unbounded) — lower confidence (stale conversation), but still
             a resolvable lead, so still surfaced rather than parked.

        Returns (provider_message_id_or_None, strategy), where strategy is
        one of "context_id", "phone_recent", "phone_any", "unmatched" — the
        caller logs this so which path fired is always debuggable.
        """
        if context_id:
            anchor = await self.repo.get_earliest_by_provider_message_id(context_id)
            if anchor:
                return context_id, "context_id"

        if not from_phone:
            return None, "unmatched"

        recent_cutoff = datetime.utcnow() - timedelta(hours=_REPLY_PHONE_MATCH_WINDOW_HOURS)
        anchor = await self.repo.get_latest_whatsapp_sent_by_phone(from_phone, since=recent_cutoff)
        if anchor:
            return anchor.provider_message_id, "phone_recent"

        anchor = await self.repo.get_latest_whatsapp_sent_by_phone(from_phone, since=None)
        if anchor:
            return anchor.provider_message_id, "phone_any"

        return None, "unmatched"

    async def is_whatsapp_session_window_active(self, lead_id: int) -> bool:
        """Server-side guard for freeform (non-template) WhatsApp sends —
        True only if this lead has an inbound 'replied' WhatsApp event within
        the last WHATSAPP_SESSION_WINDOW_HOURS. Belt-and-suspenders: Meta's
        own Graph API also rejects an out-of-window freeform send, but
        checking here avoids the round-trip and gives a clear 400 instead of
        surfacing Meta's error text. Reads the same communication_events
        rows the Inbox already polls — no new table."""
        last_reply = await self.repo.get_latest_by_lead_and_event_type(lead_id, "replied", channel="whatsapp")
        if last_reply is None:
            return False
        return (datetime.utcnow() - last_reply.occurred_at) <= timedelta(hours=WHATSAPP_SESSION_WINDOW_HOURS)

    async def record_inbound_status(
        self,
        provider_message_id: str,
        event_type: str,
        channel: str,
        provider: Optional[str] = None,
        payload: Optional[dict] = None,
        dedup_key: Optional[str] = None,
    ) -> Optional[CommunicationEventSchema]:
        """Record a delivered/read/replied/failed event from a provider
        webhook, matched to the original *_sent event via provider_message_id.

        Only ever creates a row in communication_events — no other table is
        touched, and no journey/engine logic is invoked here.

        ``dedup_key``: for multi-occurrence event types (currently WhatsApp
        'replied' — a thread can get several genuine separate replies, so
        provider_message_id+event_type uniqueness deliberately does not
        apply, see migration d2e3f4a5b6c8), pass the inbound message's own
        provider-side id here instead of relying on provider_message_id+
        event_type for idempotency. Omit for single-occurrence types
        (delivered/read/clicked/bounced/complained/sent) — unchanged
        behavior.

        Returns ``None`` (a no-op) when:
          - no *_sent event exists for this provider_message_id (unmatched
            inbound event — there is nothing to attach it to), or
          - this exact (provider_message_id, event_type) [or dedup_key, if
            given] was already recorded (idempotent — providers retry
            webhook delivery), or
          - a concurrent delivery of the same webhook lost the race and hit
            the uq_communication_events_pmid_event_type DB constraint
            (belt-and-suspenders for the check-then-insert race above).
        """
        anchor = await self.repo.get_earliest_by_provider_message_id(provider_message_id)
        if anchor is None:
            return None

        if dedup_key:
            if await self.repo.exists_by_event_type_and_dedup_key(event_type, dedup_key):
                return None
        else:
            if await self.repo.exists_by_provider_message_id_and_type(provider_message_id, event_type):
                return None

        enriched_payload = dict(payload or {})
        anchor_payload = anchor.payload or {}
        enriched_payload.setdefault("template_key", anchor_payload.get("template_key"))
        enriched_payload.setdefault("source", anchor_payload.get("source", "automation"))
        enriched_payload.setdefault("status", event_type)
        # Immutable snapshot from the anchor (Decision 1) — never re-derived
        # or looked up here, only copied forward from whatever was written
        # at send time.
        enriched_payload.setdefault("stage", anchor_payload.get("stage"))
        # Display fields (subject/body/from/to) forwarded from the original
        # *_sent event so JAWIS's timeline can render a delivered/read/
        # clicked/bounced/complained card without needing the *_sent event
        # too — same rationale as template_key/stage above.
        enriched_payload.setdefault("subject", anchor_payload.get("subject"))
        enriched_payload.setdefault("body", anchor_payload.get("body"))
        enriched_payload.setdefault("from", anchor_payload.get("from"))
        enriched_payload.setdefault("to", anchor_payload.get("to"))
        if dedup_key:
            enriched_payload["dedup_key"] = dedup_key

        try:
            return await self.create(
                CommunicationEventCreateSchema(
                    running_instance_id=str(anchor.running_instance_id) if anchor.running_instance_id else None,
                    journey_id=str(anchor.journey_id) if anchor.journey_id else None,
                    lead_id=anchor.lead_id,
                    node_id=anchor.node_id,
                    event_type=event_type,
                    channel=channel,
                    provider=provider,
                    provider_message_id=provider_message_id,
                    payload=enriched_payload,
                )
            )
        except IntegrityError:
            await self.repo.session.rollback()
            logger.info(
                "record_inbound_status: concurrent duplicate for provider_message_id=%s event_type=%s "
                "— already recorded by a parallel request, treating as idempotent no-op",
                provider_message_id, event_type,
            )
            return None

    async def record_email_reply(
        self,
        gmail_message_id: str,
        gmail_thread_id: str,
        in_reply_to: Optional[str],
        references: List[str],
        subject: str,
        body: str,
        from_address: str,
        received_at: Optional[datetime],
    ) -> Optional[CommunicationEventSchema]:
        """Record an inbound Gmail reply as a REPLIED CommunicationEvent.

        Matching priority (see app/gmail_sync/service.py for the Gmail-side
        header extraction):
          1. In-Reply-To / References headers against a stored outbound
             rfc822_message_id (captured at send time by message_routes.py).
          2. Gmail threadId against a previously-matched event in the same
             thread (handles a 2nd+ reply once the 1st has been matched).
        A literal "provider_message_id" string match against email headers
        is NOT implemented — Resend's internal id never appears in RFC822
        headers a recipient's reply would carry (only the rfc822 Message-ID
        does), so that "priority" isn't realizable and isn't faked here.

        Unlike record_inbound_status(), idempotency here is NOT
        provider_message_id+event_type (a thread can have multiple genuine
        separate replies — see migration d2e3f4a5b6c8) — it's keyed on the
        inbound Gmail message's own Message-ID instead.

        Returns None when: this exact Gmail message was already recorded,
        or no anchor could be matched (nothing to correlate the reply to).
        """
        if await self.repo.exists_replied_by_gmail_message_id(gmail_message_id):
            return None

        anchor = None
        for candidate in [in_reply_to, *references]:
            if not candidate:
                continue
            anchor = await self.repo.get_by_payload_rfc822_message_id(candidate)
            if anchor:
                break

        if anchor is None and gmail_thread_id:
            anchor = await self.repo.get_by_payload_gmail_thread_id(gmail_thread_id)

        if anchor is None:
            return None

        anchor_payload = anchor.payload or {}
        try:
            return await self.create(
                CommunicationEventCreateSchema(
                    running_instance_id=str(anchor.running_instance_id) if anchor.running_instance_id else None,
                    journey_id=str(anchor.journey_id) if anchor.journey_id else None,
                    lead_id=anchor.lead_id,
                    node_id=anchor.node_id,
                    event_type="replied",
                    channel=anchor.channel,
                    provider=anchor.provider,
                    provider_message_id=anchor.provider_message_id,
                    payload={
                        "gmail_message_id": gmail_message_id,
                        "gmail_thread_id": gmail_thread_id,
                        "in_reply_to": in_reply_to,
                        "references": references,
                        "subject": subject,
                        "body": body,
                        "from": from_address,
                        # The monitored inbox that received this reply — completes the
                        # from/to pair for display, mirroring the *_sent events' shape.
                        "to": get_settings().GMAIL_MONITOR_EMAIL,
                        "received_at": received_at.isoformat() if received_at else None,
                        "template_key": anchor_payload.get("template_key"),
                        "source": anchor_payload.get("source", "automation"),
                        "status": "replied",
                        # Immutable snapshot from the anchor (Decision 1).
                        "stage": anchor_payload.get("stage"),
                    },
                )
            )
        except IntegrityError:
            await self.repo.session.rollback()
            logger.info(
                "record_email_reply: concurrent duplicate for gmail_message_id=%s — "
                "already recorded by a parallel sync run, treating as idempotent no-op",
                gmail_message_id,
            )
            return None

    def _to_schema(self, event: CommunicationEvent) -> CommunicationEventSchema:
        return CommunicationEventSchema(
            id=str(event.id),
            running_instance_id=str(event.running_instance_id) if event.running_instance_id else None,
            journey_id=str(event.journey_id) if event.journey_id else None,
            lead_id=event.lead_id,
            node_id=event.node_id,
            event_type=event.event_type,
            channel=event.channel,
            provider=event.provider,
            provider_message_id=event.provider_message_id,
            payload=event.payload or {},
            occurred_at=event.occurred_at,
            created_at=event.created_at,
            updated_at=event.updated_at,
            jawis_synced_at=event.jawis_synced_at,
        )
