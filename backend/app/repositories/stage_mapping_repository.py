from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.stage_mapping import StageMapping


class StageMappingRepository(BaseRepository[StageMapping]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, StageMapping)

    async def get(self, id: UUID) -> Optional[StageMapping]:
        result = await self.session.execute(select(StageMapping).where(StageMapping.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, journey_id: Optional[UUID] = None
    ) -> List[StageMapping]:
        query = select(StageMapping).offset(skip).limit(limit).order_by(StageMapping.sort_order)
        if journey_id:
            query = query.where(StageMapping.journey_id == journey_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj: StageMapping) -> StageMapping:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: StageMapping) -> StageMapping:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(delete(StageMapping).where(StageMapping.id == id))
        await self.session.commit()
        return result.rowcount > 0

    async def get_by_journey(self, journey_id: UUID) -> List[StageMapping]:
        result = await self.session.execute(
            select(StageMapping)
            .where(StageMapping.journey_id == journey_id)
            .order_by(StageMapping.sort_order)
        )
        return list(result.scalars().all())

    async def get_by_stage_key(self, stage_key: str) -> List[StageMapping]:
        result = await self.session.execute(
            select(StageMapping).where(StageMapping.stage_key == stage_key)
        )
        return list(result.scalars().all())
