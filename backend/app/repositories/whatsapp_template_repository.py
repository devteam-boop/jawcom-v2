from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
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
        search: Optional[str] = None,
    ) -> List[WhatsAppTemplate]:
        """Admin/full listing (Phase 1) — every status, every version, not
        filtered down to "latest approved" (see get_latest_approved_per_family
        for the client-facing equivalent)."""
        query = (
            select(WhatsAppTemplate)
            .offset(skip).limit(limit)
            .order_by(WhatsAppTemplate.template_name.asc(), WhatsAppTemplate.version.desc())
        )
        if status:
            query = query.where(WhatsAppTemplate.status == status)
        if language:
            query = query.where(WhatsAppTemplate.language == language)
        if search:
            query = query.where(WhatsAppTemplate.template_name.ilike(f"%{search}%"))
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

    async def get_latest_version_by_name(self, template_name: str, language: str) -> Optional[WhatsAppTemplate]:
        """Highest version row for this (name, language) regardless of
        status — used to compute the next version number when creating a
        new draft (Phase 2/5), and to find "the family" a new draft joins."""
        result = await self.session.execute(
            select(WhatsAppTemplate)
            .where(
                WhatsAppTemplate.template_name == template_name,
                WhatsAppTemplate.language == language,
            )
            .order_by(WhatsAppTemplate.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_approved_by_name(self, template_name: str, language: str) -> Optional[WhatsAppTemplate]:
        """Phase 5's send-time resolution: among versions of this
        (name, language) that are APPROVED, the highest version — never the
        overall-latest version if that one isn't APPROVED (an older Approved
        version must remain sendable while a newer resubmission is under
        review)."""
        result = await self.session.execute(
            select(WhatsAppTemplate)
            .where(
                WhatsAppTemplate.template_name == template_name,
                WhatsAppTemplate.language == language,
                WhatsAppTemplate.status == "APPROVED",
            )
            .order_by(WhatsAppTemplate.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_approved_by_family(self, family_id: UUID) -> Optional[WhatsAppTemplate]:
        """Same rule as get_latest_approved_by_name, keyed by family_id
        instead — used by TemplateService.get_template()'s dual-mode
        resolution so Journey Engine nodes configured with a family_id
        automatically follow whichever version is currently approved."""
        result = await self.session.execute(
            select(WhatsAppTemplate)
            .where(
                WhatsAppTemplate.family_id == family_id,
                WhatsAppTemplate.status == "APPROVED",
            )
            .order_by(WhatsAppTemplate.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_versions_by_family(self, family_id: UUID) -> List[WhatsAppTemplate]:
        """Full version history for one template family (Phase 5), newest first."""
        result = await self.session.execute(
            select(WhatsAppTemplate)
            .where(WhatsAppTemplate.family_id == family_id)
            .order_by(WhatsAppTemplate.version.desc())
        )
        return list(result.scalars().all())

    async def get_latest_approved_per_family(self, language: Optional[str] = None) -> List[WhatsAppTemplate]:
        """Phase 6 — the client-facing (JAWIS/manual-picker) listing: for
        every family that has at least one APPROVED version, only its
        highest-version APPROVED row. Never an older Approved version, never
        a family whose highest version happens to be Pending/Rejected while
        an older version is still Approved (that older one IS returned —
        see get_latest_approved_by_family's docstring for why).

        Implemented in Python rather than a SQL window function: template
        catalogs are small (Meta itself caps templates per WABA in the
        hundreds), so a straightforward fetch-all-approved +
        keep-highest-per-family pass is simpler to read/verify than a
        DISTINCT ON/window-function query, at negligible cost.
        """
        query = (
            select(WhatsAppTemplate)
            .where(WhatsAppTemplate.status == "APPROVED")
            .order_by(WhatsAppTemplate.family_id, WhatsAppTemplate.version.desc())
        )
        if language:
            query = query.where(WhatsAppTemplate.language == language)
        result = await self.session.execute(query)

        latest_per_family: dict = {}
        for row in result.scalars().all():
            if row.family_id not in latest_per_family:
                latest_per_family[row.family_id] = row
        return list(latest_per_family.values())

    async def increment_usage(self, template_id: UUID, when: datetime) -> None:
        """Phase 7 — called from MetaWhatsAppIntegration.execute() after a
        confirmed (non-failed) Meta send, for both Manual Send and
        Journey/Automation."""
        await self.session.execute(
            update(WhatsAppTemplate)
            .where(WhatsAppTemplate.id == template_id)
            .values(usage_count=WhatsAppTemplate.usage_count + 1, last_used_at=when)
        )
        await self.session.commit()

    async def create(self, obj: WhatsAppTemplate) -> WhatsAppTemplate:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: WhatsAppTemplate) -> WhatsAppTemplate:
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
