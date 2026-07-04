from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flow_version import FlowVersion
from app.repositories.flow_version_repository import FlowVersionRepository
from app.flow_definitions.schemas import (
    FlowVersionSchema,
    FlowVersionCreateSchema,
)


class FlowVersionService:
    def __init__(self, session: AsyncSession):
        self.repo = FlowVersionRepository(session)

    async def create(self, data: FlowVersionCreateSchema) -> FlowVersionSchema:
        latest = await self.repo.get_latest_version(UUID(data.flow_definition_id))
        next_version = (latest.version + 1) if latest else 1

        version = FlowVersion(
            id=uuid4(),
            flow_definition_id=UUID(data.flow_definition_id),
            version=next_version,
            definition=data.definition,
            change_log=data.change_log,
        )
        created = await self.repo.create(version)
        return self._to_schema(created)

    async def get(self, version_id: UUID) -> FlowVersionSchema:
        version = await self.repo.get(version_id)
        if not version:
            raise ValueError(f"FlowVersion {version_id} not found")
        return self._to_schema(version)

    async def delete(self, version_id: UUID) -> bool:
        return await self.repo.delete(version_id)

    async def list(
        self, skip: int = 0, limit: int = 100,
        flow_definition_id: Optional[UUID] = None,
    ) -> List[FlowVersionSchema]:
        versions = await self.repo.get_all(
            skip=skip, limit=limit, flow_definition_id=flow_definition_id
        )
        return [self._to_schema(v) for v in versions]

    def _to_schema(self, version: FlowVersion) -> FlowVersionSchema:
        return FlowVersionSchema(
            id=str(version.id),
            flow_definition_id=str(version.flow_definition_id),
            version=version.version,
            definition=version.definition or {},
            change_log=version.change_log,
            created_at=version.created_at,
            updated_at=version.updated_at,
        )
