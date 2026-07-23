from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.running_journey_instance import RunningJourneyInstance, InstanceStatus


class RunningInstanceRepository(BaseRepository[RunningJourneyInstance]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RunningJourneyInstance)

    async def get(self, id: UUID) -> Optional[RunningJourneyInstance]:
        result = await self.session.execute(
            select(RunningJourneyInstance).where(RunningJourneyInstance.id == id)
        )
        return result.scalar_one_or_none()

    async def get_for_update(self, id: UUID) -> Optional[RunningJourneyInstance]:
        """Same as ``get`` but takes a row lock (``SELECT ... FOR UPDATE``).

        Used only by ExecutionEngine._resume_from — a concurrent resume of
        the same instance (a scheduler tick racing a manual API resume, or
        two scheduler processes) would otherwise both read the same
        `current_node_id`/`resume_at`/`wait_condition` and both proceed to
        traverse, double-executing downstream nodes. Taking the lock here
        serializes that decision; a second concurrent caller blocks until the
        first's transaction commits, then sees the already-cleared pause
        state and has nothing left to act on. Not used by the plain `get()`
        call sites elsewhere (API reads, etc.) — this would be an
        unnecessary locking cost for those.
        """
        result = await self.session.execute(
            select(RunningJourneyInstance)
            .where(RunningJourneyInstance.id == id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100,
        journey_id: Optional[UUID] = None,
        status: Optional[str] = None,
        lead_id: Optional[int] = None,
    ) -> List[RunningJourneyInstance]:
        query = select(RunningJourneyInstance).offset(skip).limit(limit).order_by(
            RunningJourneyInstance.started_at.desc()
        )
        if journey_id:
            query = query.where(RunningJourneyInstance.journey_id == journey_id)
        if status:
            query = query.where(RunningJourneyInstance.status == status)
        if lead_id:
            query = query.where(RunningJourneyInstance.lead_id == lead_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj: RunningJourneyInstance) -> RunningJourneyInstance:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: RunningJourneyInstance) -> RunningJourneyInstance:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(RunningJourneyInstance).where(RunningJourneyInstance.id == id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def get_by_lead(self, lead_id: int) -> List[RunningJourneyInstance]:
        result = await self.session.execute(
            select(RunningJourneyInstance)
            .where(RunningJourneyInstance.lead_id == lead_id)
            .order_by(RunningJourneyInstance.started_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_by_lead_and_journey(
        self, lead_id: int, journey_id: UUID
    ) -> Optional[RunningJourneyInstance]:
        result = await self.session.execute(
            select(RunningJourneyInstance).where(
                RunningJourneyInstance.lead_id == lead_id,
                RunningJourneyInstance.journey_id == journey_id,
                RunningJourneyInstance.status == InstanceStatus.RUNNING.value,
            )
        )
        return result.scalar_one_or_none()
