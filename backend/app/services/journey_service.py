from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journey import Journey, JourneyStatus
from app.repositories.journey_repository import JourneyRepository
from app.journeys.schemas import (
    JourneySchema,
    JourneyCreateSchema,
    JourneyUpdateSchema,
)


class JourneyService:
    def __init__(self, session: AsyncSession):
        self.repo = JourneyRepository(session)

    async def create(self, data: JourneyCreateSchema) -> JourneySchema:
        journey = Journey(
            id=uuid4(),
            name=data.name,
            description=data.description,
            status=JourneyStatus.DRAFT.value,
            trigger_type=data.trigger_type,
            trigger_value=data.trigger_value,
            flow_definition_id=UUID(data.flow_definition_id) if data.flow_definition_id else None,
            config=data.config or {},
        )
        created = await self.repo.create(journey)
        return self._to_schema(created)

    async def get(self, journey_id: UUID) -> JourneySchema:
        journey = await self.repo.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        return self._to_schema(journey)

    async def update(self, journey_id: UUID, data: JourneyUpdateSchema) -> JourneySchema:
        journey = await self.repo.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None and field != "flow_definition_id":
                setattr(journey, field, value)

        if "flow_definition_id" in update_data:
            journey.flow_definition_id = UUID(data.flow_definition_id) if data.flow_definition_id else None

        updated = await self.repo.update(journey)
        return self._to_schema(updated)

    async def delete(self, journey_id: UUID) -> bool:
        return await self.repo.delete(journey_id)

    async def list(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[JourneySchema]:
        journeys = await self.repo.get_all(skip=skip, limit=limit, status=status)
        return [self._to_schema(j) for j in journeys]

    async def activate(self, journey_id: UUID) -> JourneySchema:
        journey = await self.repo.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        journey.status = JourneyStatus.ACTIVE.value
        updated = await self.repo.update(journey)
        return self._to_schema(updated)

    async def pause(self, journey_id: UUID) -> JourneySchema:
        journey = await self.repo.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        journey.status = JourneyStatus.PAUSED.value
        updated = await self.repo.update(journey)
        return self._to_schema(updated)

    async def archive(self, journey_id: UUID) -> JourneySchema:
        journey = await self.repo.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        journey.status = JourneyStatus.ARCHIVED.value
        updated = await self.repo.update(journey)
        return self._to_schema(updated)

    def _to_schema(self, journey: Journey) -> JourneySchema:
        return JourneySchema(
            id=str(journey.id),
            name=journey.name,
            description=journey.description,
            status=journey.status,
            trigger_type=journey.trigger_type,
            trigger_value=journey.trigger_value,
            flow_definition_id=str(journey.flow_definition_id) if journey.flow_definition_id else None,
            config=journey.config or {},
            created_at=journey.created_at,
            updated_at=journey.updated_at,
        )
