from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.flow_version import FlowVersion


class FlowVersionRepository(BaseRepository[FlowVersion]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FlowVersion)

    async def get(self, id: UUID) -> Optional[FlowVersion]:
        result = await self.session.execute(select(FlowVersion).where(FlowVersion.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, flow_definition_id: Optional[UUID] = None
    ) -> List[FlowVersion]:
        query = select(FlowVersion).offset(skip).limit(limit).order_by(FlowVersion.version.desc())
        if flow_definition_id:
            query = query.where(FlowVersion.flow_definition_id == flow_definition_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj: FlowVersion) -> FlowVersion:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: FlowVersion) -> FlowVersion:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(delete(FlowVersion).where(FlowVersion.id == id))
        await self.session.commit()
        return result.rowcount > 0

    async def get_by_definition(self, flow_definition_id: UUID) -> List[FlowVersion]:
        result = await self.session.execute(
            select(FlowVersion)
            .where(FlowVersion.flow_definition_id == flow_definition_id)
            .order_by(FlowVersion.version.desc())
        )
        return list(result.scalars().all())

    async def get_latest_version(self, flow_definition_id: UUID) -> Optional[FlowVersion]:
        result = await self.session.execute(
            select(FlowVersion)
            .where(FlowVersion.flow_definition_id == flow_definition_id)
            .order_by(FlowVersion.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
