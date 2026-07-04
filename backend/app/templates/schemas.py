from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TemplateSchema(BaseModel):
    id: str = Field(..., description="Template ID")
    channel: str = Field(..., description="Template channel")
    name: str = Field(..., description="Template name")
    subject: Optional[str] = Field(None, description="Template subject (for email)")
    body: str = Field(..., description="Template body")
    module: str = Field(..., description="Template module")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class TemplateCreateSchema(BaseModel):
    name: str = Field(..., description="Template name")
    channel: str = Field(..., description="Template channel")
    subject: Optional[str] = Field(None, description="Template subject (for email)")
    content: str = Field(..., description="Template content with variables")


class TemplateUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Template name")
    subject: Optional[str] = Field(None, description="Template subject (for email)")
    content: Optional[str] = Field(None, description="Template content with variables")


class TemplateVersionSchema(BaseModel):
    id: str = Field(..., description="Version ID")
    template_id: str = Field(..., description="Template ID")
    body: str = Field(..., description="Template body")
    created_at: datetime = Field(..., description="Version creation timestamp")


class RenderTemplateRequest(BaseModel):
    template_id: str = Field(..., description="Template ID to render")
    variables: Dict[str, Any] = Field(..., description="Variables to substitute in template")


class TemplateUsageSchema(BaseModel):
    journey_ids: List[str] = Field(default_factory=list, description="Journey IDs using this template")
    flow_ids: List[str] = Field(default_factory=list, description="Flow IDs using this template")
    campaign_ids: List[str] = Field(default_factory=list, description="Campaign IDs using this template")
