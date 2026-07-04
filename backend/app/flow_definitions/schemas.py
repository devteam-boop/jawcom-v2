"""Pydantic schemas for Flow Definition Engine."""

from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class FlowDefinitionStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ── Flow Definition ──────────────────────────────────────────────


class FlowDefinitionSchema(BaseModel):
    id: str = Field(..., description="Flow definition ID")
    name: str = Field(..., description="Flow definition name")
    description: Optional[str] = Field(None, description="Flow definition description")
    status: FlowDefinitionStatus = Field(..., description="Flow definition status")
    definition: Dict[str, Any] = Field(..., description="Flow definition JSON")
    version: int = Field(..., description="Current version number")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class FlowDefinitionCreateSchema(BaseModel):
    name: str = Field(..., description="Flow definition name")
    description: Optional[str] = Field(None, description="Flow definition description")
    definition: Dict[str, Any] = Field(..., description="Flow definition JSON")


class FlowDefinitionUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Flow definition name")
    description: Optional[str] = Field(None, description="Flow definition description")
    status: Optional[FlowDefinitionStatus] = Field(None, description="Flow definition status")
    definition: Optional[Dict[str, Any]] = Field(None, description="Flow definition JSON")


# ── Flow Version ─────────────────────────────────────────────────


class FlowVersionSchema(BaseModel):
    id: str = Field(..., description="Flow version ID")
    flow_definition_id: str = Field(..., description="Flow definition ID")
    version: int = Field(..., description="Version number")
    definition: Dict[str, Any] = Field(..., description="Snapshot of the flow definition")
    change_log: Optional[str] = Field(None, description="Change log for this version")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class FlowVersionCreateSchema(BaseModel):
    flow_definition_id: str = Field(..., description="Flow definition ID")
    definition: Dict[str, Any] = Field(..., description="Snapshot of the flow definition")
    change_log: Optional[str] = Field(None, description="Change log for this version")


# ── Flow Execution Log ───────────────────────────────────────────


class FlowExecutionLogSchema(BaseModel):
    id: str = Field(..., description="Execution log ID")
    flow_definition_id: str = Field(..., description="Flow definition ID")
    flow_version_id: Optional[str] = Field(None, description="Flow version ID")
    running_instance_id: str = Field(..., description="Running journey instance ID")
    lead_id: int = Field(..., description="Lead ID (references existing leads table)")
    node_id: str = Field(..., description="Node ID within the flow")
    status: str = Field(..., description="Execution status (success, failed, skipped)")
    input: Optional[Dict[str, Any]] = Field(default={}, description="Input data for the node")
    output: Optional[Dict[str, Any]] = Field(default={}, description="Output data from the node")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    executed_at: datetime = Field(..., description="Execution timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class FlowExecutionLogCreateSchema(BaseModel):
    flow_definition_id: str = Field(..., description="Flow definition ID")
    flow_version_id: Optional[str] = Field(None, description="Flow version ID")
    running_instance_id: str = Field(..., description="Running journey instance ID")
    lead_id: int = Field(..., description="Lead ID")
    node_id: str = Field(..., description="Node ID within the flow")
    status: str = Field(..., description="Execution status (success, failed, skipped)")
    input: Optional[Dict[str, Any]] = Field(default={}, description="Input data")
    output: Optional[Dict[str, Any]] = Field(default={}, description="Output data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
