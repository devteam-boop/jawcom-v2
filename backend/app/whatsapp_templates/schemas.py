from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WhatsAppTemplateSchema(BaseModel):
    id: str
    provider_template_id: Optional[str] = None
    template_name: str
    language: str
    category: Optional[str] = None
    status: str
    header_type: Optional[str] = None
    header_text: Optional[str] = None
    header_media_url: Optional[str] = None
    body: str
    footer: Optional[str] = None
    buttons: List[Dict[str, Any]] = Field(default_factory=list)
    variables: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    family_id: str
    version: int
    quality_rating: Optional[str] = None
    rejection_reason: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
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
    last_error: Optional[str] = None


class WhatsAppTemplatePreviewRequest(BaseModel):
    variables: Dict[str, str] = Field(default_factory=dict)


class WhatsAppTemplatePreviewResponse(BaseModel):
    header: Optional[str] = None
    body: str
    footer: Optional[str] = None


class WhatsAppTemplateCreateSchema(BaseModel):
    """Phase 2 — Create Template screen's backend contract. Always produces
    a local-only DRAFT row (no Meta call — see WhatsAppTemplateService.
    create_draft()). If a family with this exact (template_name, language)
    already exists, this becomes its next version instead of a new family."""
    template_name: str
    category: str = Field(..., description="Meta category, e.g. MARKETING/UTILITY/AUTHENTICATION")
    language: str
    header_type: Optional[str] = Field(None, description="TEXT/IMAGE/VIDEO/DOCUMENT, or omit for no header")
    header_text: Optional[str] = Field(None, description="Only used when header_type == TEXT")
    header_media_url: Optional[str] = Field(
        None, description="Stub only — no upload flow yet; submit_to_meta() rejects non-TEXT headers for now",
    )
    body: str
    footer: Optional[str] = None
    buttons: List[Dict[str, Any]] = Field(default_factory=list)
    # Positional example values Meta requires at submission time for a body
    # with variables, e.g. ["John", "Acme Corp"] for a body containing
    # {{1}}/{{2}}. Length should match the number of variables found in body.
    examples: List[str] = Field(default_factory=list)


class WhatsAppTemplateVersionsResponse(BaseModel):
    family_id: str
    versions: List[WhatsAppTemplateSchema]
