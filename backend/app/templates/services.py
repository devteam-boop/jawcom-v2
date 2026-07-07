"""Template Engine services."""

from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template, TemplateStatus
from app.repositories.template_repository import TemplateRepository
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


class TemplateService:
    """Service for managing communication templates (backed by the `templates` table)."""

    def __init__(self, session: AsyncSession):
        self.repo = TemplateRepository(session)
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
        """Raises TemplateNotFoundError if the template does not exist."""
        template = await self.repo.get(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")
        return self._to_schema(template)

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
        self, channel: Optional[str] = None, status: Optional[str] = None
    ) -> List[TemplateSchema]:
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
        )
