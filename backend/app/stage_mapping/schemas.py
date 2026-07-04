"""Pydantic schemas for Stage Mapping Engine."""

from typing import Optional, Any, Dict
from uuid import UUID as _UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class StageMappingSchema(BaseModel):
    id: str = Field(..., description="Stage mapping ID")
    journey_id: str = Field(..., description="Journey ID")
    name: Optional[str] = Field(None, description="Stage mapping name")
    description: Optional[str] = Field(None, description="Stage mapping description")
    stage_key: str = Field(..., description="Lead stage key this mapping responds to")
    template_id: Optional[str] = Field(None, description="Template ID (references custom_templates)")
    channel: Optional[str] = Field(None, description="Communication channel (email, sms, whatsapp)")
    sort_order: int = Field(0, description="Execution order within the journey")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Additional configuration")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class StageMappingCreateSchema(BaseModel):
    journey_id: str = Field(..., description="Journey ID")
    name: Optional[str] = Field(None, description="Stage mapping name")
    description: Optional[str] = Field(None, description="Stage mapping description")
    stage_key: str = Field(..., description="Lead stage key this mapping responds to")
    template_id: Optional[str] = Field(None, description="Template ID (references custom_templates)")
    channel: Optional[str] = Field(None, description="Communication channel (email, sms, whatsapp)")
    sort_order: int = Field(0, description="Execution order within the journey")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Additional configuration")

    @field_validator("journey_id", "template_id")
    @classmethod
    def validate_uuid_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                _UUID(v)
            except (ValueError, AttributeError):
                raise ValueError(f"'{v}' is not a valid UUID")
        return v


class StageMappingUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Stage mapping name")
    description: Optional[str] = Field(None, description="Stage mapping description")
    stage_key: Optional[str] = Field(None, description="Lead stage key")
    template_id: Optional[str] = Field(None, description="Template ID")
    channel: Optional[str] = Field(None, description="Communication channel")
    sort_order: Optional[int] = Field(None, description="Execution order")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")

    @field_validator("template_id")
    @classmethod
    def validate_template_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                _UUID(v)
            except (ValueError, AttributeError):
                raise ValueError(f"'{v}' is not a valid UUID")
        return v
