"""Template Engine services."""

from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.orm import Session
from .schemas import (
    TemplateSchema, 
    TemplateCreateSchema, 
    TemplateUpdateSchema,
    RenderTemplateRequest,
    TemplateUsageSchema
)
from .validators import TemplateValidator
from .renderer import TemplateRenderer
from .exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
    TemplateInUseError,
    InvalidTemplateStatusError
)
from ..models import CustomTemplate


class TemplateService:
    """Service for managing templates using JAWIS custom_templates table."""

    JAWIS_MODULE = 'communications'

    def __init__(self, db_session: Session):
        """Initialize template service."""
        self.db = db_session
        self.validator = TemplateValidator()
        self.renderer = TemplateRenderer()

    def create_template(self, template_data: TemplateCreateSchema) -> TemplateSchema:
        """
        Create a new template.

        Args:
            template_data: Template creation data

        Returns:
            Created template schema

        Raises:
            TemplateValidationError: If validation fails
        """
        # Validate template name
        self.validator.validate_template_name(template_data.name)

        # Validate template content
        variables = self.validator.validate_template_content(
            template_data.content,
            template_data.channel
        )

        # Validate email template specific requirements
        if template_data.channel == "email":
            self.validator.validate_email_template(
                template_data.subject or "",
                template_data.content
            )

        # Create template in custom_templates table
        template = CustomTemplate(
            id=uuid.uuid4(),
            name=template_data.name,
            channel=template_data.channel,
            subject=template_data.subject,
            body=template_data.content,
            module=self.JAWIS_MODULE,
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return self._model_to_schema(template)

    def get_template(self, template_id: str) -> TemplateSchema:
        """
        Get template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template schema

        Raises:
            TemplateNotFoundError: If template not found
        """
        template = self.db.query(CustomTemplate).filter(CustomTemplate.id == template_id).first()
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        variables = self.validator.validate_template_content(template.body, template.channel)
        return self._model_to_schema(template)

    def update_template(self, template_id: str, update_data: TemplateUpdateSchema) -> TemplateSchema:
        """
        Update template.

        Args:
            template_id: Template ID
            update_data: Update data

        Returns:
            Updated template schema

        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If validation fails
        """
        template = self.db.query(CustomTemplate).filter(CustomTemplate.id == template_id).first()
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        # Update fields if provided
        if update_data.name is not None:
            self.validator.validate_template_name(update_data.name)
            template.name = update_data.name

        if update_data.content is not None:
            variables = self.validator.validate_template_content(
                update_data.content,
                template.channel
            )
            template.body = update_data.content

        if update_data.subject is not None and template.channel == "email":
            self.validator.validate_email_template(
                update_data.subject,
                template.body
            )
            template.subject = update_data.subject

        self.db.commit()
        self.db.refresh(template)

        variables = self.validator.validate_template_content(template.body, template.channel)
        return self._model_to_schema(template)

    def delete_template(self, template_id: str) -> bool:
        """
        Delete template if not in use.

        Args:
            template_id: Template ID

        Returns:
            True if deleted

        Raises:
            TemplateNotFoundError: If template not found
            TemplateInUseError: If template is currently in use
        """
        template = self.db.query(CustomTemplate).filter(CustomTemplate.id == template_id).first()
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        # Check if template is in use
        usage = self.get_template_usage(template_id)
        if usage.journey_ids or usage.flow_ids or usage.campaign_ids:
            raise TemplateInUseError("Template is currently in use and cannot be deleted")

        self.db.delete(template)
        self.db.commit()
        return True

    def render_template(self, request: RenderTemplateRequest) -> str:
        """
        Render template with variables.

        Args:
            request: Render request with template ID and variables

        Returns:
            Rendered content

        Raises:
            TemplateNotFoundError: If template not found
        """
        template = self.db.query(CustomTemplate).filter(CustomTemplate.id == request.template_id).first()
        if not template:
            raise TemplateNotFoundError(f"Template {request.template_id} not found")

        if template.channel == "email":
            result = self.renderer.render_email(
                template.subject or "",
                template.body,
                request.variables
            )
            return result["content"]  # For simplicity, returning content only
        else:
            return self.renderer.render_whatsapp(template.body, request.variables)

    def get_template_usage(self, template_id: str) -> TemplateUsageSchema:
        """
        Get template usage information.

        Args:
            template_id: Template ID

        Returns:
            Template usage schema
        """
        # In a real implementation, this would query related models
        # For now, returning empty lists
        return TemplateUsageSchema(
            journey_ids=[],
            flow_ids=[],
            campaign_ids=[]
        )

    def list_templates(self, channel: Optional[str] = None) -> List[TemplateSchema]:
        """
        List templates for JawCom's module.

        Args:
            channel: Optional channel filter

        Returns:
            List of template schemas
        """
        query = self.db.query(CustomTemplate).filter(
            CustomTemplate.module == self.JAWIS_MODULE
        )

        if channel:
            query = query.filter(CustomTemplate.channel == channel)

        templates = query.all()
        result = []

        for template in templates:
            try:
                variables = self.validator.validate_template_content(template.body, template.channel)
                result.append(self._model_to_schema(template))
            except TemplateValidationError:
                # Skip invalid templates
                continue

        return result

    def _model_to_schema(self, template: CustomTemplate) -> TemplateSchema:
        """Convert template model to schema."""
        return TemplateSchema(
            id=str(template.id),
            channel=template.channel,
            name=template.name,
            subject=template.subject,
            body=template.body,
            module=template.module,
            created_at=template.created_at,
        )
