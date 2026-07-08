from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_events.schemas import (
    CommunicationEventCreateSchema,
    CommunicationEventSchema,
)
from app.models.communication_event import CommunicationEvent
from app.repositories.communication_event_repository import CommunicationEventRepository


class CommunicationEventService:
    def __init__(self, session: AsyncSession):
        self.repo = CommunicationEventRepository(session)

    async def create(self, data: CommunicationEventCreateSchema) -> CommunicationEventSchema:
        event = CommunicationEvent(
            id=uuid4(),
            running_instance_id=UUID(data.running_instance_id),
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
            recorded (idempotent — providers retry webhook delivery).
        """
        anchor = await self.repo.get_earliest_by_provider_message_id(provider_message_id)
        if anchor is None:
            return None

        if await self.repo.exists_by_provider_message_id_and_type(provider_message_id, event_type):
            return None

        return await self.create(
            CommunicationEventCreateSchema(
                running_instance_id=str(anchor.running_instance_id),
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

    def _to_schema(self, event: CommunicationEvent) -> CommunicationEventSchema:
        return CommunicationEventSchema(
            id=str(event.id),
            running_instance_id=str(event.running_instance_id),
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
