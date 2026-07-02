"""Typed event models for business events from JAWIS."""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import Field, validator
from .base_event import BaseEvent


class LeadCreatedEvent(BaseEvent):
    """Event fired when a new lead is created in JAWIS."""
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = 'lead.created'
        if 'source' not in data:
            data['source'] = 'jawis'
        super().__init__(**data)
    
    def get_event_key(self) -> str:
        return "lead.created"
    
    def validate_payload(self) -> bool:
        """Validate lead created event payload."""
        required_fields = ['lead_id', 'stage_key']
        for field in required_fields:
            if field not in self.data:
                raise ValueError(f"Missing required field: {field}")
        return True
    
    @property
    def lead_id(self) -> str:
        """Get lead ID from event data."""
        return self.data['lead_id']
    
    @property
    def stage_key(self) -> str:
        """Get stage key from event data."""
        return self.data['stage_key']
    
    @property
    def lead_name(self) -> Optional[str]:
        """Get lead name from event data."""
        return self.data.get('lead_name')
    
    @property
    def lead_email(self) -> Optional[str]:
        """Get lead email from event data."""
        return self.data.get('lead_email')
    
    @property
    def lead_phone(self) -> Optional[str]:
        """Get lead phone from event data."""
        return self.data.get('lead_phone')


class LeadStageChangedEvent(BaseEvent):
    """Event fired when a lead moves between stages in JAWIS."""
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = 'lead.stage_changed'
        if 'source' not in data:
            data['source'] = 'jawis'
        super().__init__(**data)
    
    def get_event_key(self) -> str:
        return "lead.stage_changed"
    
    def validate_payload(self) -> bool:
        """Validate lead stage changed event payload."""
        required_fields = ['lead_id', 'from_stage_key', 'to_stage_key']
        for field in required_fields:
            if field not in self.data:
                raise ValueError(f"Missing required field: {field}")
        return True
    
    @property
    def lead_id(self) -> str:
        """Get lead ID from event data."""
        return self.data['lead_id']
    
    @property
    def from_stage_key(self) -> str:
        """Get previous stage key from event data."""
        return self.data['from_stage_key']
    
    @property
    def to_stage_key(self) -> str:
        """Get new stage key from event data."""
        return self.data['to_stage_key']
    
    @property
    def changed_by(self) -> Optional[str]:
        """Get user who changed the stage."""
        return self.data.get('changed_by')
    
    @property
    def change_reason(self) -> Optional[str]:
        """Get reason for stage change."""
        return self.data.get('change_reason')


class LeadAssignedEvent(BaseEvent):
    """Event fired when a lead is assigned to a new owner in JAWIS."""
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = 'lead.assigned'
        if 'source' not in data:
            data['source'] = 'jawis'
        super().__init__(**data)
    
    def get_event_key(self) -> str:
        return "lead.assigned"
    
    def validate_payload(self) -> bool:
        """Validate lead assigned event payload."""
        required_fields = ['lead_id', 'assigned_to']
        for field in required_fields:
            if field not in self.data:
                raise ValueError(f"Missing required field: {field}")
        return True
    
    @property
    def lead_id(self) -> str:
        """Get lead ID from event data."""
        return self.data['lead_id']
    
    @property
    def assigned_to(self) -> str:
        """Get new assignee from event data."""
        return self.data['assigned_to']
    
    @property
    def assigned_by(self) -> Optional[str]:
        """Get user who made the assignment."""
        return self.data.get('assigned_by')
    
    @property
    def previous_assignee(self) -> Optional[str]:
        """Get previous assignee."""
        return self.data.get('previous_assignee')


class LeadRequirementMetEvent(BaseEvent):
    """Event fired when a lead satisfies a requirement in JAWIS."""
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = 'lead.requirement_met'
        if 'source' not in data:
            data['source'] = 'jawis'
        super().__init__(**data)
    
    def get_event_key(self) -> str:
        return "lead.requirement_met"
    
    def validate_payload(self) -> bool:
        """Validate lead requirement met event payload."""
        required_fields = ['lead_id', 'requirement_key']
        for field in required_fields:
            if field not in self.data:
                raise ValueError(f"Missing required field: {field}")
        return True
    
    @property
    def lead_id(self) -> str:
        """Get lead ID from event data."""
        return self.data['lead_id']
    
    @property
    def requirement_key(self) -> str:
        """Get requirement key from event data."""
        return self.data['requirement_key']
    
    @property
    def requirement_value(self) -> Optional[Any]:
        """Get requirement value."""
        return self.data.get('requirement_value')
    
    @property
    def met_by(self) -> Optional[str]:
        """Get user who satisfied the requirement."""
        return self.data.get('met_by')


# Event type registry for dynamic event creation
EVENT_TYPE_REGISTRY = {
    'lead.created': LeadCreatedEvent,
    'lead.stage_changed': LeadStageChangedEvent,
    'lead.assigned': LeadAssignedEvent,
    'lead.requirement_met': LeadRequirementMetEvent,
}


def create_event_from_type(event_type: str, **kwargs) -> BaseEvent:
    """
    Create an event instance from event type string.
    
    Args:
        event_type: The event type string (e.g., 'lead.created')
        **kwargs: Event data and metadata
        
    Returns:
        BaseEvent: Instance of the appropriate event class
        
    Raises:
        ValueError: If event type is not registered
    """
    if event_type not in EVENT_TYPE_REGISTRY:
        raise ValueError(f"Unknown event type: {event_type}")
    
    event_class = EVENT_TYPE_REGISTRY[event_type]
    return event_class(**kwargs)


def get_supported_event_types() -> list[str]:
    """Get list of all supported event types."""
    return list(EVENT_TYPE_REGISTRY.keys())
