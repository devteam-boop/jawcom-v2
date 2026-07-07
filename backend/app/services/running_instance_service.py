from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.running_journey_instance import RunningJourneyInstance, InstanceStatus
from app.repositories.running_instance_repository import RunningInstanceRepository
from app.runtime.schemas import (
    RunningInstanceSchema,
    RunningInstanceCreateSchema,
    RunningInstanceUpdateSchema,
)


class RunningInstanceService:
    def __init__(self, session: AsyncSession):
        self.repo = RunningInstanceRepository(session)

    async def create(self, data: RunningInstanceCreateSchema) -> RunningInstanceSchema:
        instance = RunningJourneyInstance(
            id=uuid4(),
            lead_id=data.lead_id,
            journey_id=UUID(data.journey_id),
            current_stage_mapping_id=UUID(data.current_stage_mapping_id) if data.current_stage_mapping_id else None,
            status=InstanceStatus.RUNNING.value,
            data=data.data or {},
        )
        created = await self.repo.create(instance)
        return self._to_schema(created)

    async def get(self, instance_id: UUID) -> RunningInstanceSchema:
        instance = await self.repo.get(instance_id)
        if not instance:
            raise ValueError(f"RunningInstance {instance_id} not found")
        return self._to_schema(instance)

    async def update(
        self, instance_id: UUID, data: RunningInstanceUpdateSchema
    ) -> RunningInstanceSchema:
        instance = await self.repo.get(instance_id)
        if not instance:
            raise ValueError(f"RunningInstance {instance_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if field == "current_stage_mapping_id" and value is not None:
                    value = UUID(value)
                setattr(instance, field, value)

        updated = await self.repo.update(instance)
        return self._to_schema(updated)

    async def delete(self, instance_id: UUID) -> bool:
        return await self.repo.delete(instance_id)

    async def list(
        self, skip: int = 0, limit: int = 100,
        journey_id: Optional[UUID] = None,
        status: Optional[str] = None,
        lead_id: Optional[int] = None,
    ) -> List[RunningInstanceSchema]:
        instances = await self.repo.get_all(
            skip=skip, limit=limit, journey_id=journey_id,
            status=status, lead_id=lead_id,
        )
        return [self._to_schema(i) for i in instances]

    async def complete(self, instance_id: UUID) -> RunningInstanceSchema:
        instance = await self.repo.get(instance_id)
        if not instance:
            raise ValueError(f"RunningInstance {instance_id} not found")
        instance.status = InstanceStatus.COMPLETED.value
        instance.completed_at = datetime.utcnow()
        updated = await self.repo.update(instance)
        return self._to_schema(updated)

    async def wait(self, instance_id: UUID, instance_data: dict) -> RunningInstanceSchema:
        """Transition instance to ``waiting`` status and store resume metadata.

        Called by the engine when a Wait node returns ``status="skipped"``.
        The scheduler will pick up this instance and resume traversal when
        ``instance.data.resume_at`` is reached.
        """
        instance = await self.repo.get(instance_id)
        if not instance:
            raise ValueError(f"RunningInstance {instance_id} not found")
        instance.status = InstanceStatus.WAITING.value
        instance.data = instance_data
        updated = await self.repo.update(instance)
        return self._to_schema(updated)

    async def wait_approval(self, instance_id: UUID, instance_data: dict) -> RunningInstanceSchema:
        """Transition instance to ``waiting_approval`` status and store approval metadata."""
        instance = await self.repo.get(instance_id)
        if not instance:
            raise ValueError(f"RunningInstance {instance_id} not found")
        instance.status = InstanceStatus.WAITING_APPROVAL.value
        instance.data = instance_data
        updated = await self.repo.update(instance)
        return self._to_schema(updated)

    async def wait_task(self, instance_id: UUID, instance_data: dict) -> RunningInstanceSchema:
        """Transition instance to ``waiting_task`` status and store task metadata."""
        instance = await self.repo.get(instance_id)
        if not instance:
            raise ValueError(f"RunningInstance {instance_id} not found")
        instance.status = InstanceStatus.WAITING_TASK.value
        instance.data = instance_data
        updated = await self.repo.update(instance)
        return self._to_schema(updated)

    async def find_waiting(
        self, now: Optional[datetime] = None,
    ) -> List[RunningInstanceSchema]:
        """Return all instances in ``waiting`` status whose resume_at <= now."""
        if now is None:
            now = datetime.utcnow()
        now_iso = now.isoformat()
        instances = await self.repo.get_all(status=InstanceStatus.WAITING.value)
        due = []
        for inst in instances:
            data = inst.data or {}
            resume_at_str = data.get("resume_at")
            if resume_at_str and resume_at_str <= now_iso:
                due.append(self._to_schema(inst))
        return due

    async def fail(self, instance_id: UUID) -> RunningInstanceSchema:
        instance = await self.repo.get(instance_id)
        if not instance:
            raise ValueError(f"RunningInstance {instance_id} not found")
        instance.status = InstanceStatus.FAILED.value
        instance.completed_at = datetime.utcnow()
        updated = await self.repo.update(instance)
        return self._to_schema(updated)

    def _to_schema(self, instance: RunningJourneyInstance) -> RunningInstanceSchema:
        return RunningInstanceSchema(
            id=str(instance.id),
            lead_id=instance.lead_id,
            journey_id=str(instance.journey_id),
            current_stage_mapping_id=str(instance.current_stage_mapping_id) if instance.current_stage_mapping_id else None,
            status=instance.status,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            data=instance.data or {},
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )
