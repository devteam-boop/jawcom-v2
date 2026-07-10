from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WhatsAppTemplateSchema(BaseModel):
    id: str
    provider_template_id: str
    template_name: str
    language: str
    category: Optional[str] = None
    status: str
    header_type: Optional[str] = None
    body: str
    footer: Optional[str] = None
    buttons: List[Dict[str, Any]] = Field(default_factory=list)
    variables: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WhatsAppTemplateSyncResultSchema(BaseModel):
    scanned: int
    created: int
    updated: int
    unchanged: int
    last_synced_at: datetime


class WhatsAppTemplateSyncStatusSchema(BaseModel):
    last_synced_at: Optional[datetime] = None


class WhatsAppTemplatePreviewRequest(BaseModel):
    variables: Dict[str, str] = Field(default_factory=dict)


class WhatsAppTemplatePreviewResponse(BaseModel):
    header: Optional[str] = None
    body: str
    footer: Optional[str] = None
