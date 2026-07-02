"""Event system for handling business events from JAWIS."""

from .base_event import BaseEvent, EventHandler, EventResult, EventPriority, EventStatus
from .event_types import (
    LeadCreatedEvent,
    LeadStageChangedEvent,
    LeadAssignedEvent,
    LeadRequirementMetEvent,
    create_event_from_type,
    get_supported_event_types,
    EVENT_TYPE_REGISTRY
)
from .dispatcher import EventDispatcher, get_dispatcher, reset_dispatcher
from .handlers import CommunicationEventHandler, LoggingEventHandler, MetricsEventHandler

__all__ = [
    # Base classes
    "BaseEvent",
    "EventHandler", 
    "EventResult",
    "EventPriority",
    "EventStatus",
    
    # Event types
    "LeadCreatedEvent",
    "LeadStageChangedEvent", 
    "LeadAssignedEvent",
    "LeadRequirementMetEvent",
    "create_event_from_type",
    "get_supported_event_types",
    "EVENT_TYPE_REGISTRY",
    
    # Dispatcher
    "EventDispatcher",
    "get_dispatcher",
    "reset_dispatcher",
    
    # Handlers
    "CommunicationEventHandler",
    "LoggingEventHandler",
    "MetricsEventHandler"
]
