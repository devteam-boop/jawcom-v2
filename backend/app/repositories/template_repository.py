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

    async def get_active_siblings(self, family_id: UUID, exclude_id: UUID) -> List[Template]:
        """Other rows in this family that are currently ACTIVE. Used by
        activate_and_deactivate_siblings() below, under that method's
        family-level lock, to enforce "only one ACTIVE version per family"."""
        result = await self.session.execute(
            select(Template).where(
                Template.family_id == family_id,
                Template.status == "active",
                Template.id != exclude_id,
            )
        )
        return list(result.scalars().all())

    async def activate_and_deactivate_siblings(self, template_id: UUID, family_id: UUID) -> Optional[Template]:
        """Atomically activate ``template_id`` and deactivate every other
        ACTIVE row in ``family_id``, as a single transaction.

        Two concurrent Activate calls for the same family would otherwise
        race: both could read "no active sibling yet" before either commits,
        and both end up ACTIVE. ``SELECT ... FOR UPDATE`` on every row in
        the family takes a row-level lock for the rest of this transaction,
        so a second concurrent call for the same family blocks here until
        the first one commits (releasing the lock) — the second call then
        re-reads under its own lock and correctly deactivates what the first
        call just activated. A single commit at the end (not one per row)
        keeps the whole operation inside that one locked transaction.
        """
        await self.session.execute(
            select(Template.id).where(Template.family_id == family_id).with_for_update()
        )

        template = await self.session.get(Template, template_id)
        if template is None:
            return None

        siblings = await self.get_active_siblings(family_id, exclude_id=template_id)
        for sibling in siblings:
            sibling.status = "inactive"

        template.status = "active"

        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def get_active_by_family(self, family_id: UUID) -> Optional[Template]:
        """The email family's current ACTIVE version, if any — the new
        get_template() fallback for a Journey/flow node configured with a
        family_id instead of one pinned row (see TemplateService.get_template).
        Scoped to channel="email": this lifecycle only applies to email."""
        result = await self.session.execute(
            select(Template).where(
                Template.family_id == family_id,
                Template.status == "active",
                Template.channel == "email",
            )
        )
        return result.scalar_one_or_none()
