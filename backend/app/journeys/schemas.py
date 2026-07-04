"""Pydantic schemas for Journey Engine."""

from typing import Optional, Any, Dict
from uuid import UUID as _UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class JourneyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class JourneySchema(BaseModel):
    id: str = Field(..., description="Journey ID")
    name: str = Field(..., description="Journey name")
    description: Optional[str] = Field(None, description="Journey description")
    status: JourneyStatus = Field(..., description="Journey status")
    trigger_type: str = Field(..., description="Trigger type")
    trigger_value: Optional[str] = Field(None, description="Trigger value")
    flow_definition_id: Optional[str] = Field(None, description="Linked flow definition ID")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Journey configuration")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class JourneyCreateSchema(BaseModel):
    name: str = Field(..., description="Journey name")
    description: Optional[str] = Field(None, description="Journey description")
    trigger_type: str = Field(..., description="Trigger type (e.g. lead_created, lead_stage_changed)")
    trigger_value: Optional[str] = Field(None, description="Trigger value (e.g. stage key)")
    flow_definition_id: Optional[str] = Field(None, description="Linked flow definition ID")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Journey configuration")

    @field_validator("flow_definition_id")
    @classmethod
    def validate_flow_definition_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                _UUID(v)
            except (ValueError, AttributeError):
                raise ValueError(f"'{v}' is not a valid UUID")
        return v


class JourneyUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Journey name")
    description: Optional[str] = Field(None, description="Journey description")
    status: Optional[JourneyStatus] = Field(None, description="Journey status")
    trigger_type: Optional[str] = Field(None, description="Trigger type")
    trigger_value: Optional[str] = Field(None, description="Trigger value")
    flow_definition_id: Optional[str] = Field(None, description="Linked flow definition ID")
    config: Optional[Dict[str, Any]] = Field(None, description="Journey configuration")

    @field_validator("flow_definition_id")
    @classmethod
    def validate_flow_definition_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                _UUID(v)
            except (ValueError, AttributeError):
                raise ValueError(f"'{v}' is not a valid UUID")
        return v
