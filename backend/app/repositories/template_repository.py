from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.template import Template


class TemplateRepository(BaseRepository[Template]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Template)

    async def get(self, id: UUID) -> Optional[Template]:
        result = await self.session.execute(select(Template).where(Template.id == id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        channel: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Template]:
        query = select(Template).offset(skip).limit(limit).order_by(Template.created_at.desc())
        if channel:
            query = query.where(Template.channel == channel)
        if status:
            query = query.where(Template.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj: Template) -> Template:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: Template) -> Template:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(delete(Template).where(Template.id == id))
        await self.session.commit()
        return result.rowcount > 0
