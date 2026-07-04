from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.journey import Journey, JourneyStatus


class JourneyRepository(BaseRepository[Journey]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Journey)

    async def get(self, id: UUID) -> Optional[Journey]:
        result = await self.session.execute(select(Journey).where(Journey.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[Journey]:
        query = select(Journey).offset(skip).limit(limit).order_by(Journey.created_at.desc())
        if status:
            query = query.where(Journey.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj: Journey) -> Journey:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: Journey) -> Journey:
        await self.session.flush()
        await self.session.refresh(obj)
        await self.session.commit()
        return obj

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(delete(Journey).where(Journey.id == id))
        await self.session.commit()
        return result.rowcount > 0

    async def count(self, status: Optional[str] = None) -> int:
        query = select(Journey)
        if status:
            query = query.where(Journey.status == status)
        result = await self.session.execute(query)
        return len(result.scalars().all())
