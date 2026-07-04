"""Pydantic schemas for Flow Definition Engine."""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class NodeType(str, Enum):
    """Supported node types."""
    TRIGGER = "trigger"
    DELAY = "delay"
    CONDITION = "condition"
    SEND_WHATSAPP = "send_whatsapp"
    SEND_EMAIL = "send_email"
    NOTIFICATION = "notification"
    WAIT = "wait"
    END = "end"


class NodeData(BaseModel):
    """Base node data structure."""
    pass


class TriggerNodeData(NodeData):
    """Trigger node specific data."""
    event_type: str = Field(..., description="Type of event that triggers the flow")
    criteria: Dict[str, Any] = Field(default_factory=dict, description="Trigger criteria")


class DelayNodeData(NodeData):
    """Delay node specific data."""
    duration: int = Field(..., description="Delay duration in seconds")
    unit: str = Field("seconds", description="Time unit (seconds, minutes, hours, days)")


class ConditionNodeData(NodeData):
    """Condition node specific data."""
    condition_type: str = Field(..., description="Type of condition")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Condition parameters")
    true_branch: str = Field(..., description="Node ID for true condition")
    false_branch: str = Field(..., description="Node ID for false condition")


class SendTemplateNodeData(NodeData):
    """Send template node data (for both email and WhatsApp)."""
    template_id: str = Field(..., description="Template ID to send")
    recipient_variable: str = Field("lead", description="Variable containing recipient info")


class NotificationNodeData(NodeData):
    """Notification node specific data."""
    message: str = Field(..., description="Notification message")
    recipients: List[str] = Field(default_factory=list, description="Recipient user IDs")


class WaitNodeData(NodeData):
    """Wait node specific data."""
    wait_type: str = Field(..., description="Type of wait condition")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Wait parameters")


class NodeSchema(BaseModel):
    """Schema for a flow node."""
    id: str = Field(..., description="Unique node ID")
    type: NodeType = Field(..., description="Node type")
    data: Union[
        TriggerNodeData,
        DelayNodeData,
        ConditionNodeData,
        SendTemplateNodeData,
        NotificationNodeData,
        WaitNodeData
    ] = Field(..., description="Node-specific data")
    position: Dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0}, description="Node position")
    label: Optional[str] = Field(None, description="Node label for display")


class EdgeSchema(BaseModel):
    """Schema for a connection between nodes."""
    id: str = Field(..., description="Unique edge ID")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_handle: Optional[str] = Field(None, description="Source handle ID")
    target_handle: Optional[str] = Field(None, description="Target handle ID")


class FlowStatus(str, Enum):
    """Flow status options."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class FlowDefinitionSchema(BaseModel):
    """Schema for flow definition."""
    id: str = Field(..., description="Flow definition ID")
    name: str = Field(..., description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")
    nodes: List[NodeSchema] = Field(..., description="Flow nodes")
    edges: List[EdgeSchema] = Field(..., description="Flow edges")
    status: FlowStatus = Field(..., description="Flow status")
    version: int = Field(..., description="Flow version")
    is_active: bool = Field(..., description="Whether this is the active version")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    workspace_id: str = Field(..., description="Workspace ID")


class FlowVersionSchema(BaseModel):
    """Schema for flow version data."""
    id: str = Field(..., description="Flow version ID")
    flow_id: str = Field(..., description="Flow ID")
    version: int = Field(..., description="Flow version")
    is_active: bool = Field(..., description="Whether this is the active version")
    status: FlowStatus = Field(..., description="Version status")
    created_at: datetime = Field(..., description="Creation timestamp")


class FlowCreateSchema(BaseModel):
    """Schema for creating a new flow."""
    name: str = Field(..., description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")
    workspace_id: str = Field(..., description="Workspace ID")


class FlowUpdateSchema(BaseModel):
    """Schema for updating a flow."""
    name: Optional[str] = Field(None, description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")
    nodes: Optional[List[NodeSchema]] = Field(None, description="Flow nodes")
    edges: Optional[List[EdgeSchema]] = Field(None, description="Flow edges")


class FlowPublishSchema(BaseModel):
    """Schema for publishing a flow."""
    flow_id: str = Field(..., description="Flow ID to publish")
