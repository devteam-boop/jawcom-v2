import copy
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journey import Journey, JourneyStatus
from app.models.flow_definition import FlowDefinition, FlowDefinitionStatus
from app.repositories.journey_repository import JourneyRepository
from app.repositories.flow_definition_repository import FlowDefinitionRepository
from app.journeys.schemas import (
    JourneySchema,
    JourneyCreateSchema,
    JourneyUpdateSchema,
)


class JourneyDeleteBlockedError(Exception):
    """Raised when attempting to delete a journey that is not safe to delete."""


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

    async def delete(self, journey_id: UUID, deleted_by: Optional[str] = None) -> bool:
        journey = await self.repo.get(journey_id)
        if not journey:
            return False
        if journey.status == JourneyStatus.ACTIVE.value:
            raise JourneyDeleteBlockedError("Deactivate this journey before deleting.")
        return await self.repo.soft_delete(journey_id, deleted_by=deleted_by)

    async def duplicate(self, journey_id: UUID) -> JourneySchema:
        journey = await self.repo.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")

        session = self.repo.session
        try:
            new_flow_definition_id = None
            if journey.flow_definition_id:
                flow_repo = FlowDefinitionRepository(session)
                flow_def = await flow_repo.get(journey.flow_definition_id)
                if flow_def:
                    new_flow_def = FlowDefinition(
                        id=uuid4(),
                        name=f"{flow_def.name} (Copy)",
                        description=flow_def.description,
                        status=FlowDefinitionStatus.DRAFT.value,
                        definition=self._clone_flow_definition_json(flow_def.definition or {}),
                        version=1,
                    )
                    session.add(new_flow_def)
                    new_flow_definition_id = new_flow_def.id

            new_journey = Journey(
                id=uuid4(),
                name=f"{journey.name} (Copy)",
                description=journey.description,
                status=JourneyStatus.DRAFT.value,
                trigger_type=journey.trigger_type,
                trigger_value=journey.trigger_value,
                flow_definition_id=new_flow_definition_id,
                config=copy.deepcopy(journey.config) if journey.config else {},
            )
            session.add(new_journey)
            await session.flush()
            await session.commit()
            await session.refresh(new_journey)
        except Exception:
            await session.rollback()
            raise

        return self._to_schema(new_journey)

    @staticmethod
    def _clone_flow_definition_json(definition: dict) -> dict:
        """Deep-copies a flow definition JSON, regenerating node and edge IDs.

        Node references inside edges (from/to, source/target) are remapped
        to the new node IDs so the duplicated flow is independently editable.
        """
        cloned = copy.deepcopy(definition)
        nodes = cloned.get("nodes") or []
        edges = cloned.get("edges") or []

        id_map = {}
        for node in nodes:
            old_id = node.get("id")
            new_id = str(uuid4())
            if old_id is not None:
                id_map[old_id] = new_id
            node["id"] = new_id

        for edge in edges:
            edge["id"] = str(uuid4())
            for key in ("from", "to", "source", "target"):
                if edge.get(key) in id_map:
                    edge[key] = id_map[edge[key]]

        cloned["nodes"] = nodes
        cloned["edges"] = edges
        return cloned

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
