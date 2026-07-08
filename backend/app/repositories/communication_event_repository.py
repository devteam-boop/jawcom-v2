from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.communication_event import CommunicationEvent


class CommunicationEventRepository(BaseRepository[CommunicationEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, CommunicationEvent)

    async def get(self, id: UUID) -> Optional[CommunicationEvent]:
        result = await self.session.execute(
            select(CommunicationEvent).where(CommunicationEvent.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, obj: CommunicationEvent) -> CommunicationEvent:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_all(
        self, skip: int = 0, limit: int = 100,
        running_instance_id: Optional[UUID] = None,
        journey_id: Optional[UUID] = None,
        lead_id: Optional[int] = None,
        event_type: Optional[str] = None,
        provider_message_id: Optional[str] = None,
    ) -> List[CommunicationEvent]:
        query = select(CommunicationEvent).offset(skip).limit(limit).order_by(
            CommunicationEvent.occurred_at.asc()
        )
        if running_instance_id:
            query = query.where(CommunicationEvent.running_instance_id == running_instance_id)
        if journey_id:
            query = query.where(CommunicationEvent.journey_id == journey_id)
        if lead_id:
            query = query.where(CommunicationEvent.lead_id == lead_id)
        if event_type:
            query = query.where(CommunicationEvent.event_type == event_type)
        if provider_message_id:
            query = query.where(CommunicationEvent.provider_message_id == provider_message_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_earliest_by_provider_message_id(self, provider_message_id: str) -> Optional[CommunicationEvent]:
        """Return the first-recorded event for a provider_message_id (the
        original *_sent event) — used as the anchor to copy
        running_instance_id/journey_id/lead_id/node_id onto an inbound
        delivered/read/replied/failed event."""
        result = await self.session.execute(
            select(CommunicationEvent)
            .where(CommunicationEvent.provider_message_id == provider_message_id)
            .order_by(CommunicationEvent.occurred_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def exists_by_provider_message_id_and_type(self, provider_message_id: str, event_type: str) -> bool:
        """Idempotency check — prevents duplicate rows when a provider
        retries the same webhook delivery."""
        result = await self.session.execute(
            select(CommunicationEvent.id)
            .where(
                CommunicationEvent.provider_message_id == provider_message_id,
                CommunicationEvent.event_type == event_type,
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
