from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stage_mapping import StageMapping
from app.repositories.stage_mapping_repository import StageMappingRepository
from app.stage_mapping.schemas import (
    StageMappingSchema,
    StageMappingCreateSchema,
    StageMappingUpdateSchema,
)


class StageMappingService:
    def __init__(self, session: AsyncSession):
        self.repo = StageMappingRepository(session)

    async def create(self, data: StageMappingCreateSchema) -> StageMappingSchema:
        mapping = StageMapping(
            id=uuid4(),
            journey_id=UUID(data.journey_id),
            name=data.name or '',
            description=data.description,
            stage_key=data.stage_key,
            template_id=UUID(data.template_id) if data.template_id else None,
            channel=data.channel,
            sort_order=data.sort_order,
            config=data.config or {},
        )
        created = await self.repo.create(mapping)
        return self._to_schema(created)

    async def get(self, mapping_id: UUID) -> StageMappingSchema:
        mapping = await self.repo.get(mapping_id)
        if not mapping:
            raise ValueError(f"StageMapping {mapping_id} not found")
        return self._to_schema(mapping)

    async def update(
        self, mapping_id: UUID, data: StageMappingUpdateSchema
    ) -> StageMappingSchema:
        mapping = await self.repo.get(mapping_id)
        if not mapping:
            raise ValueError(f"StageMapping {mapping_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if field == "template_id" and value is not None:
                    value = UUID(value)
                setattr(mapping, field, value)

        updated = await self.repo.update(mapping)
        return self._to_schema(updated)

    async def delete(self, mapping_id: UUID) -> bool:
        return await self.repo.delete(mapping_id)

    async def list(
        self, skip: int = 0, limit: int = 100, journey_id: Optional[UUID] = None
    ) -> List[StageMappingSchema]:
        mappings = await self.repo.get_all(
            skip=skip, limit=limit, journey_id=journey_id
        )
        return [self._to_schema(m) for m in mappings]

    def _to_schema(self, mapping: StageMapping) -> StageMappingSchema:
        return StageMappingSchema(
            id=str(mapping.id),
            journey_id=str(mapping.journey_id),
            name=mapping.name or None,
            description=mapping.description,
            stage_key=mapping.stage_key,
            template_id=str(mapping.template_id) if mapping.template_id else None,
            channel=mapping.channel,
            sort_order=mapping.sort_order,
            config=mapping.config or {},
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        )
