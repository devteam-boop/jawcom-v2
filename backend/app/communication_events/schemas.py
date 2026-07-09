from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CommunicationEventCreateSchema(BaseModel):
    running_instance_id: Optional[str] = None
    journey_id: Optional[str] = None
    lead_id: int
    node_id: Optional[str] = None
    event_type: str
    channel: str = "system"
    provider: Optional[str] = None
    provider_message_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class CommunicationEventSchema(BaseModel):
    id: str
    running_instance_id: Optional[str] = None
    journey_id: Optional[str] = None
    lead_id: int
    node_id: Optional[str] = None
    event_type: str
    channel: str
    provider: Optional[str] = None
    provider_message_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
