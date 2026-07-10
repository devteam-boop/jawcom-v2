from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.whatsapp_template import WhatsAppTemplate


class WhatsAppTemplateRepository(BaseRepository[WhatsAppTemplate]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WhatsAppTemplate)

    async def get(self, id: UUID) -> Optional[WhatsAppTemplate]:
        result = await self.session.execute(
            select(WhatsAppTemplate).where(WhatsAppTemplate.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[WhatsAppTemplate]:
        query = (
            select(WhatsAppTemplate)
            .offset(skip).limit(limit)
            .order_by(WhatsAppTemplate.template_name.asc())
        )
        if status:
            query = query.where(WhatsAppTemplate.status == status)
        if language:
            query = query.where(WhatsAppTemplate.language == language)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_provider_template_id(self, provider_template_id: str) -> Optional[WhatsAppTemplate]:
        """Sync dedupe key — see WhatsAppTemplateService.sync_from_meta()."""
        result = await self.session.execute(
            select(WhatsAppTemplate).where(
                WhatsAppTemplate.provider_template_id == provider_template_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name_and_language(self, template_name: str, language: str) -> Optional[WhatsAppTemplate]:
        """Send-time lookup key — see message_routes.py send_whatsapp()."""
        result = await self.session.execute(
            select(WhatsAppTemplate).where(
                WhatsAppTemplate.template_name == template_name,
                WhatsAppTemplate.language == language,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, obj: WhatsAppTemplate) -> WhatsAppTemplate:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: WhatsAppTemplate) -> WhatsAppTemplate:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
