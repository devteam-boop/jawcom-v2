from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TemplateSchema(BaseModel):
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    channel: str = Field(..., description="Template channel (email|sms|whatsapp|push)")
    status: str = Field(..., description="Template status (draft|active|inactive)")
    subject: Optional[str] = Field(None, description="Template subject (for email)")
    content: str = Field(..., description="Template body with {{variable}} placeholders")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class TemplateCreateSchema(BaseModel):
    name: str = Field(..., description="Template name")
    channel: str = Field(..., description="Template channel (email|sms|whatsapp|push)")
    subject: Optional[str] = Field(None, description="Template subject (for email)")
    content: str = Field(..., description="Template content with variables")
    status: Optional[str] = Field(None, description="Template status (defaults to draft)")


class TemplateUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Template name")
    subject: Optional[str] = Field(None, description="Template subject (for email)")
    content: Optional[str] = Field(None, description="Template content with variables")
    channel: Optional[str] = Field(None, description="Template channel (email|sms|whatsapp|push)")
    status: Optional[str] = Field(None, description="Template status (draft|active|inactive)")


class RenderTemplateRequest(BaseModel):
    template_id: str = Field(..., description="Template ID to render")
    variables: Dict[str, Any] = Field(..., description="Variables to substitute in template")


class TemplateUsageSchema(BaseModel):
    stage_mapping_ids: List[str] = Field(default_factory=list, description="Stage mappings referencing this template")
    flow_definition_ids: List[str] = Field(default_factory=list, description="Flow definitions with a node referencing this template")
