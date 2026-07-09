import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_events.schemas import (
    CommunicationEventCreateSchema,
    CommunicationEventSchema,
)
from app.models.communication_event import CommunicationEvent
from app.repositories.communication_event_repository import CommunicationEventRepository

logger = logging.getLogger(__name__)


class CommunicationEventService:
    def __init__(self, session: AsyncSession):
        self.repo = CommunicationEventRepository(session)

    async def create(self, data: CommunicationEventCreateSchema) -> CommunicationEventSchema:
        event = CommunicationEvent(
            id=uuid4(),
            running_instance_id=UUID(data.running_instance_id) if data.running_instance_id else None,
            journey_id=UUID(data.journey_id) if data.journey_id else None,
            lead_id=data.lead_id,
            node_id=data.node_id,
            event_type=data.event_type,
            channel=data.channel,
            provider=data.provider,
            provider_message_id=data.provider_message_id,
            payload=data.payload or {},
        )
        created = await self.repo.create(event)
        return self._to_schema(created)

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
    ) -> List[CommunicationEventSchema]:
        events = await self.repo.get_all(
            skip=skip, limit=limit,
            running_instance_id=running_instance_id,
            journey_id=journey_id,
            lead_id=lead_id,
            event_type=event_type,
            provider_message_id=provider_message_id,
        )
        return [self._to_schema(e) for e in events]

    async def record_inbound_status(
        self,
        provider_message_id: str,
        event_type: str,
        channel: str,
        provider: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> Optional[CommunicationEventSchema]:
        """Record a delivered/read/replied/failed event from a provider
        webhook, matched to the original *_sent event via provider_message_id.

        Only ever creates a row in communication_events — no other table is
        touched, and no journey/engine logic is invoked here.

        Returns ``None`` (a no-op) when:
          - no *_sent event exists for this provider_message_id (unmatched
            inbound event — there is nothing to attach it to), or
          - this exact (provider_message_id, event_type) was already
            recorded (idempotent — providers retry webhook delivery), or
          - a concurrent delivery of the same webhook lost the race and hit
            the uq_communication_events_pmid_event_type DB constraint
            (belt-and-suspenders for the check-then-insert race above).
        """
        anchor = await self.repo.get_earliest_by_provider_message_id(provider_message_id)
        if anchor is None:
            return None

        if await self.repo.exists_by_provider_message_id_and_type(provider_message_id, event_type):
            return None

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
                    payload=payload or {},
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
                        "received_at": received_at.isoformat() if received_at else None,
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
        )
