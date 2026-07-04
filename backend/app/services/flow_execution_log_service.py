from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flow_execution_log import FlowExecutionLog
from app.repositories.flow_execution_log_repository import FlowExecutionLogRepository
from app.flow_definitions.schemas import (
    FlowExecutionLogSchema,
    FlowExecutionLogCreateSchema,
)


class FlowExecutionLogService:
    def __init__(self, session: AsyncSession):
        self.repo = FlowExecutionLogRepository(session)

    async def create(self, data: FlowExecutionLogCreateSchema) -> FlowExecutionLogSchema:
        log = FlowExecutionLog(
            id=uuid4(),
            flow_definition_id=UUID(data.flow_definition_id),
            flow_version_id=UUID(data.flow_version_id) if data.flow_version_id else None,
            running_instance_id=UUID(data.running_instance_id),
            lead_id=data.lead_id,
            node_id=data.node_id,
            status=data.status,
            input=data.input or {},
            output=data.output or {},
            error_message=data.error_message,
        )
        created = await self.repo.create(log)
        return self._to_schema(created)

    async def get(self, log_id: UUID) -> FlowExecutionLogSchema:
        log = await self.repo.get(log_id)
        if not log:
            raise ValueError(f"FlowExecutionLog {log_id} not found")
        return self._to_schema(log)

    async def delete(self, log_id: UUID) -> bool:
        return await self.repo.delete(log_id)

    async def list(
        self, skip: int = 0, limit: int = 100,
        flow_definition_id: Optional[UUID] = None,
        lead_id: Optional[int] = None,
        running_instance_id: Optional[UUID] = None,
    ) -> List[FlowExecutionLogSchema]:
        logs = await self.repo.get_all(
            skip=skip, limit=limit,
            flow_definition_id=flow_definition_id,
            lead_id=lead_id,
            running_instance_id=running_instance_id,
        )
        return [self._to_schema(l) for l in logs]

    def _to_schema(self, log: FlowExecutionLog) -> FlowExecutionLogSchema:
        return FlowExecutionLogSchema(
            id=str(log.id),
            flow_definition_id=str(log.flow_definition_id),
            flow_version_id=str(log.flow_version_id) if log.flow_version_id else None,
            running_instance_id=str(log.running_instance_id),
            lead_id=log.lead_id,
            node_id=log.node_id,
            status=log.status,
            input=log.input or {},
            output=log.output or {},
            error_message=log.error_message,
            executed_at=log.executed_at,
            created_at=log.created_at,
            updated_at=log.updated_at,
        )
