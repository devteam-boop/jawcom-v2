from typing import Dict, List, Optional,Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flow_definition import FlowDefinition, FlowDefinitionStatus
from app.repositories.flow_definition_repository import FlowDefinitionRepository
from app.flow_definitions.schemas import (
    FlowDefinitionSchema,
    FlowDefinitionCreateSchema,
    FlowDefinitionUpdateSchema,
    ValidationResult,
)
from app.services.flow_validation_service import FlowValidationService


class FlowDefinitionService:
    def __init__(self, session: AsyncSession):
        self.repo = FlowDefinitionRepository(session)

    async def create(self, data: FlowDefinitionCreateSchema) -> FlowDefinitionSchema:
        definition = FlowDefinition(
            id=uuid4(),
            name=data.name,
            description=data.description,
            status=FlowDefinitionStatus.DRAFT.value,
            definition=data.definition,
            version=1,
        )
        created = await self.repo.create(definition)
        return self._to_schema(created)

    async def get(self, definition_id: UUID) -> FlowDefinitionSchema:
        definition = await self.repo.get(definition_id)
        if not definition:
            raise ValueError(f"FlowDefinition {definition_id} not found")
        return self._to_schema(definition)

    async def update(
        self, definition_id: UUID, data: FlowDefinitionUpdateSchema
    ) -> FlowDefinitionSchema:
        definition = await self.repo.get(definition_id)
        if not definition:
            raise ValueError(f"FlowDefinition {definition_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(definition, field, value)

        updated = await self.repo.update(definition)
        return self._to_schema(updated)

    async def delete(self, definition_id: UUID) -> bool:
        return await self.repo.delete(definition_id)

    async def list(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[FlowDefinitionSchema]:
        definitions = await self.repo.get_all(skip=skip, limit=limit, status=status)
        return [self._to_schema(d) for d in definitions]

    async def validate(self, definition_id: UUID) -> Dict[str, Any]:
        definition = await self.repo.get(definition_id)
        if not definition:
            raise ValueError(f"FlowDefinition {definition_id} not found")
        return FlowValidationService.validate(definition.definition or {})

    async def publish(self, definition_id: UUID) -> FlowDefinitionSchema:
        definition = await self.repo.get(definition_id)
        if not definition:
            raise ValueError(f"FlowDefinition {definition_id} not found")

        result = FlowValidationService.validate(definition.definition or {})
        if not result["valid"]:
            raise ValueError(result)

        definition.status = FlowDefinitionStatus.PUBLISHED.value
        updated = await self.repo.update(definition)
        return self._to_schema(updated)

    async def archive(self, definition_id: UUID) -> FlowDefinitionSchema:
        definition = await self.repo.get(definition_id)
        if not definition:
            raise ValueError(f"FlowDefinition {definition_id} not found")
        definition.status = FlowDefinitionStatus.ARCHIVED.value
        updated = await self.repo.update(definition)
        return self._to_schema(updated)

    def _to_schema(self, definition: FlowDefinition) -> FlowDefinitionSchema:
        return FlowDefinitionSchema(
            id=str(definition.id),
            name=definition.name,
            description=definition.description,
            status=definition.status,
            definition=definition.definition or {},
            version=definition.version,
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )
