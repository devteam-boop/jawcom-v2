from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.flow_execution_log import FlowExecutionLog


class FlowExecutionLogRepository(BaseRepository[FlowExecutionLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FlowExecutionLog)

    async def get(self, id: UUID) -> Optional[FlowExecutionLog]:
        result = await self.session.execute(
            select(FlowExecutionLog).where(FlowExecutionLog.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100,
        flow_definition_id: Optional[UUID] = None,
        lead_id: Optional[int] = None,
        running_instance_id: Optional[UUID] = None,
    ) -> List[FlowExecutionLog]:
        query = select(FlowExecutionLog).offset(skip).limit(limit).order_by(
            FlowExecutionLog.executed_at.desc()
        )
        if flow_definition_id:
            query = query.where(FlowExecutionLog.flow_definition_id == flow_definition_id)
        if lead_id:
            query = query.where(FlowExecutionLog.lead_id == lead_id)
        if running_instance_id:
            query = query.where(FlowExecutionLog.running_instance_id == running_instance_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj: FlowExecutionLog) -> FlowExecutionLog:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: FlowExecutionLog) -> FlowExecutionLog:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(FlowExecutionLog).where(FlowExecutionLog.id == id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def get_by_lead(self, lead_id: int) -> List[FlowExecutionLog]:
        result = await self.session.execute(
            select(FlowExecutionLog)
            .where(FlowExecutionLog.lead_id == lead_id)
            .order_by(FlowExecutionLog.executed_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_running_instance(self, running_instance_id: UUID) -> List[FlowExecutionLog]:
        result = await self.session.execute(
            select(FlowExecutionLog)
            .where(FlowExecutionLog.running_instance_id == running_instance_id)
            .order_by(FlowExecutionLog.executed_at.asc())
        )
        return list(result.scalars().all())
