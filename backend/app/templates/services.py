"""Template Engine services."""

from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template, TemplateStatus
from app.models.whatsapp_template import WhatsAppTemplate
from app.repositories.template_repository import TemplateRepository
from app.repositories.whatsapp_template_repository import WhatsAppTemplateRepository
from app.repositories.stage_mapping_repository import StageMappingRepository
from app.repositories.flow_definition_repository import FlowDefinitionRepository
from .schemas import (
    TemplateSchema,
    TemplateCreateSchema,
    TemplateUpdateSchema,
    RenderTemplateRequest,
    TemplateUsageSchema,
)
from .validators import TemplateValidator
from .renderer import TemplateRenderer
from .exceptions import (
    TemplateNotFoundError,
    TemplateInUseError,
)


def whatsapp_template_to_schema(wa: WhatsAppTemplate) -> TemplateSchema:
    """Maps a Meta-synced WhatsApp template (whatsapp_templates,
    app/whatsapp_templates/) onto the generic TemplateSchema shape.

    Centralized here (not duplicated per-caller) because TWO things need to
    resolve a whatsapp_templates row through this exact shape:
    TemplateService.get_template()/list_templates() below (so both the HTTP
    template APIs AND Journey Engine's SendWhatsAppExecutor — which calls
    exec_ctx.template_service.get_template(UUID(template_id)) and reads
    ``.name`` — transparently resolve a whatsapp_templates id without any
    change to app/execution/*) and app/api/message_routes.py's JAWIS-facing
    template listing.
    """
    return TemplateSchema(
        id=str(wa.id),
        name=wa.template_name,
        channel="whatsapp",
        status=wa.status,
        subject=None,
        content=wa.body,
        created_at=wa.created_at,
        updated_at=wa.updated_at,
        provider_template_id=wa.provider_template_id,
        language=wa.language,
        category=wa.category,
        header_type=wa.header_type,
        footer=wa.footer,
        buttons=wa.buttons or [],
        variables=wa.variables or [],
    )


class TemplateService:
    """Service for managing communication templates (backed by the `templates` table).

    WhatsApp is special-cased throughout to read from whatsapp_templates
    instead (Meta-synced, APPROVED-only — see app/whatsapp_templates/) so
    that table is the single source of truth for WhatsApp templates: Manual
    sends (app/api/message_routes.py), Journey/Automation
    (app/execution/executors/send_whatsapp_executor.py, via
    exec_ctx.template_service — unchanged file, changed behavior only
    because it calls into this class), and both template-listing HTTP APIs
    all end up reading the same rows through get_template()/list_templates()
    below. There is still no create/update/delete for whatsapp_templates —
    those remain generic-table-only (self.repo, never self.whatsapp_repo).
    """

    def __init__(self, session: AsyncSession):
        self.repo = TemplateRepository(session)
        self.whatsapp_repo = WhatsAppTemplateRepository(session)
        self.stage_mapping_repo = StageMappingRepository(session)
        self.flow_definition_repo = FlowDefinitionRepository(session)
        self.validator = TemplateValidator()
        self.renderer = TemplateRenderer()

    async def create_template(self, data: TemplateCreateSchema) -> TemplateSchema:
        """Create a new template.

        Raises:
            TemplateValidationError: If validation fails.
        """
        self.validator.validate_template_name(data.name)
        self.validator.validate_template_content(data.content, data.channel)
        if data.channel == "email":
            self.validator.validate_email_template(data.subject or "", data.content)

        template = Template(
            id=uuid4(),
            name=data.name,
            channel=data.channel,
            subject=data.subject,
            content=data.content,
            status=data.status or TemplateStatus.DRAFT.value,
        )
        created = await self.repo.create(template)
        return self._to_schema(created)

    async def get_template(self, template_id: UUID) -> TemplateSchema:
        """Raises TemplateNotFoundError if the template does not exist in
        either the generic templates table or whatsapp_templates (checked
        in that order — a random UUID collision between the two tables is
        not realistically possible, so this never changes behavior for an
        existing generic-table id)."""
        template = await self.repo.get(template_id)
        if template:
            return self._to_schema(template)

        wa_template = await self.whatsapp_repo.get(template_id)
        if wa_template:
            return whatsapp_template_to_schema(wa_template)

        raise TemplateNotFoundError(f"Template {template_id} not found")

    async def update_template(self, template_id: UUID, data: TemplateUpdateSchema) -> TemplateSchema:
        """Raises TemplateNotFoundError / TemplateValidationError."""
        template = await self.repo.get(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        effective_channel = update_data.get("channel", template.channel)
        effective_content = update_data.get("content", template.content)
        effective_subject = update_data.get("subject", template.subject)

        if "name" in update_data:
            self.validator.validate_template_name(update_data["name"])
        if "content" in update_data or "channel" in update_data:
            self.validator.validate_template_content(effective_content, effective_channel)
        if effective_channel == "email" and ("subject" in update_data or "content" in update_data):
            self.validator.validate_email_template(effective_subject or "", effective_content)

        for field, value in update_data.items():
            setattr(template, field, value)

        updated = await self.repo.update(template)
        return self._to_schema(updated)

    async def archive_template(self, template_id: UUID) -> TemplateSchema:
        """Set status to inactive (used by the frontend's Archive action)."""
        return await self.update_template(
            template_id, TemplateUpdateSchema(status=TemplateStatus.INACTIVE.value)
        )

    async def duplicate_template(self, template_id: UUID) -> TemplateSchema:
        """Create a draft copy of an existing template."""
        template = await self.repo.get(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        copy = Template(
            id=uuid4(),
            name=f"{template.name} (Copy)",
            channel=template.channel,
            subject=template.subject,
            content=template.content,
            status=TemplateStatus.DRAFT.value,
        )
        created = await self.repo.create(copy)
        return self._to_schema(created)

    async def delete_template(self, template_id: UUID) -> bool:
        """Raises TemplateNotFoundError / TemplateInUseError."""
        template = await self.repo.get(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        usage = await self.get_template_usage(template_id)
        if usage.stage_mapping_ids or usage.flow_definition_ids:
            raise TemplateInUseError("Template is currently in use and cannot be deleted")

        return await self.repo.delete(template_id)

    async def render_template(self, request: RenderTemplateRequest) -> str:
        """Raises TemplateNotFoundError / TemplateValidationError."""
        template = await self.repo.get(UUID(request.template_id))
        if not template:
            raise TemplateNotFoundError(f"Template {request.template_id} not found")

        if template.channel == "email":
            result = self.renderer.render_email(template.subject or "", template.content, request.variables)
            return result["content"]
        return self.renderer.render_whatsapp(template.content, request.variables)

    async def get_template_usage(self, template_id: UUID) -> TemplateUsageSchema:
        """Find every stage mapping and flow node referencing this template."""
        template_id_str = str(template_id)

        stage_mappings = await self.stage_mapping_repo.get_by_template_id(template_id)
        stage_mapping_ids = [str(sm.id) for sm in stage_mappings]

        flow_definitions = await self.flow_definition_repo.get_all(skip=0, limit=1000)
        flow_definition_ids = []
        for flow_def in flow_definitions:
            nodes = (flow_def.definition or {}).get("nodes", [])
            for node in nodes:
                config = node.get("config") or {}
                if config.get("template_id") == template_id_str:
                    flow_definition_ids.append(str(flow_def.id))
                    break

        return TemplateUsageSchema(
            stage_mapping_ids=stage_mapping_ids,
            flow_definition_ids=flow_definition_ids,
        )

    async def list_templates(
        self, channel: Optional[str] = None, status: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[TemplateSchema]:
        """channel="whatsapp" is special-cased: returns only Meta-synced,
        APPROVED whatsapp_templates rows (status is forced to APPROVED,
        matching Meta's own sendable-template rule — the ``status`` param
        is ignored in this branch; ``language`` only applies here) instead
        of the generic table. Every other channel (or no channel filter)
        is unchanged generic-table behavior."""
        if channel == "whatsapp":
            wa_templates = await self.whatsapp_repo.get_all(status="APPROVED", language=language)
            return [whatsapp_template_to_schema(t) for t in wa_templates]

        templates = await self.repo.get_all(channel=channel, status=status)
        return [self._to_schema(t) for t in templates]

    def _to_schema(self, template: Template) -> TemplateSchema:
        return TemplateSchema(
            id=str(template.id),
            name=template.name,
            channel=template.channel,
            status=template.status,
            subject=template.subject,
            content=template.content,
            created_at=template.created_at,
            updated_at=template.updated_at,
            variables=self.renderer._extract_variables(template.content),
        )
