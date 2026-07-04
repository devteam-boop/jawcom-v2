"""Pydantic schemas for Running Journey Instance Engine."""

from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class InstanceStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


class RunningInstanceSchema(BaseModel):
    id: str = Field(..., description="Running instance ID")
    lead_id: int = Field(..., description="Lead ID (references existing leads table)")
    journey_id: str = Field(..., description="Journey ID")
    current_stage_mapping_id: Optional[str] = Field(None, description="Current stage mapping ID")
    status: InstanceStatus = Field(..., description="Instance status")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    data: Optional[Dict[str, Any]] = Field(default={}, description="Instance data / metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class RunningInstanceCreateSchema(BaseModel):
    lead_id: int = Field(..., description="Lead ID (references existing leads table)")
    journey_id: str = Field(..., description="Journey ID")
    current_stage_mapping_id: Optional[str] = Field(None, description="Current stage mapping ID")
    data: Optional[Dict[str, Any]] = Field(default={}, description="Instance data / metadata")


class RunningInstanceUpdateSchema(BaseModel):
    current_stage_mapping_id: Optional[str] = Field(None, description="Current stage mapping ID")
    status: Optional[InstanceStatus] = Field(None, description="Instance status")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Instance data / metadata")
