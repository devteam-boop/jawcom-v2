from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.flow_definition import FlowDefinition, FlowDefinitionStatus


class FlowDefinitionRepository(BaseRepository[FlowDefinition]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FlowDefinition)

    async def get(self, id: UUID) -> Optional[FlowDefinition]:
        result = await self.session.execute(select(FlowDefinition).where(FlowDefinition.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[FlowDefinition]:
        query = select(FlowDefinition).offset(skip).limit(limit).order_by(FlowDefinition.created_at.desc())
        if status:
            query = query.where(FlowDefinition.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj: FlowDefinition) -> FlowDefinition:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: FlowDefinition) -> FlowDefinition:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(delete(FlowDefinition).where(FlowDefinition.id == id))
        await self.session.commit()
        return result.rowcount > 0
