"""Event handlers for processing business events."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from .base_event import BaseEvent, EventHandler
from .event_types import (
    LeadCreatedEvent,
    LeadStageChangedEvent,
    LeadAssignedEvent,
    LeadRequirementMetEvent,
)

if TYPE_CHECKING:
    from app.execution.engine import ExecutionEngine

logger = logging.getLogger(__name__)


class CommunicationEventHandler(EventHandler):
    """
    Event handler that processes business events and delegates to the
    ExecutionEngine for journey orchestration.
    """

    def __init__(self, execution_engine: Optional["ExecutionEngine"] = None):
        from app.execution.engine import ExecutionEngine
        self.engine = execution_engine or ExecutionEngine()

    async def handle(self, event: BaseEvent) -> bool:
        try:
            logger.info("CommunicationEventHandler processing %s event: %s", event.get_event_key(), event.event_id)

            if isinstance(event, LeadCreatedEvent):
                return await self.engine.handle_lead_created(event)
            elif isinstance(event, LeadStageChangedEvent):
                return await self.engine.handle_lead_stage_changed(event)
            elif isinstance(event, LeadAssignedEvent):
                return await self._handle_lead_assigned(event)
            elif isinstance(event, LeadRequirementMetEvent):
                return await self._handle_lead_requirement_met(event)
            else:
                logger.warning("Unknown event type: %s", event.get_event_key())
                return False

        except Exception as e:
            logger.error("Error handling event %s: %s", event.event_id, e)
            return False

    def can_handle(self, event: BaseEvent) -> bool:
        supported_types = [
            LeadCreatedEvent,
            LeadStageChangedEvent,
            LeadAssignedEvent,
            LeadRequirementMetEvent,
        ]
        return any(isinstance(event, t) for t in supported_types)

    async def _handle_lead_assigned(self, event: LeadAssignedEvent) -> bool:
        logger.info("Lead %s assigned to %s", event.lead_id, event.assigned_to)
        logger.info("Assignment notifications are not yet implemented")
        return True

    async def _handle_lead_requirement_met(self, event: LeadRequirementMetEvent) -> bool:
        logger.info("Lead %s met requirement %s", event.lead_id, event.requirement_key)
        logger.info("Requirement-based journeys are not yet implemented")
        return True


class LoggingEventHandler(EventHandler):
    """
    Simple event handler that logs all events for debugging and auditing.
    """
    
    def __init__(self, log_level: str = "INFO"):
        """
        Initialize the logging event handler.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    async def handle(self, event: BaseEvent) -> bool:
        """
        Log the event details.
        
        Args:
            event: The event to log
            
        Returns:
            bool: Always returns True (logging doesn't fail)
        """
        log_data = {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'source': event.source,
            'timestamp': event.timestamp.isoformat(),
            'data': event.data,
            'metadata': event.metadata
        }
        
        logger.log(self.log_level, f"Event logged: {log_data}")
        return True
    
    def can_handle(self, event: BaseEvent) -> bool:
        """
        This handler can log any event.
        
        Args:
            event: The event to check
            
        Returns:
            bool: Always returns True
        """
        return True


class MetricsEventHandler(EventHandler):
    """
    Event handler that collects metrics and statistics about events.
    """
    
    def __init__(self):
        """Initialize the metrics event handler."""
        self.metrics = {
            'total_events': 0,
            'events_by_type': {},
            'events_by_source': {},
            'last_event_time': None
        }
    
    async def handle(self, event: BaseEvent) -> bool:
        """
        Collect metrics from the event.
        
        Args:
            event: The event to collect metrics from
            
        Returns:
            bool: Always returns True
        """
        self.metrics['total_events'] += 1
        
        # Count by event type
        event_type = event.get_event_key()
        self.metrics['events_by_type'][event_type] = (
            self.metrics['events_by_type'].get(event_type, 0) + 1
        )
        
        # Count by source
        source = event.source
        self.metrics['events_by_source'][source] = (
            self.metrics['events_by_source'].get(source, 0) + 1
        )
        
        # Update last event time
        self.metrics['last_event_time'] = datetime.utcnow().isoformat()
        
        return True
    
    def can_handle(self, event: BaseEvent) -> bool:
        """
        This handler can collect metrics from any event.
        
        Args:
            event: The event to check
            
        Returns:
            bool: Always returns True
        """
        return True
    
    def get_metrics(self) -> dict:
        """Get collected metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self.metrics = {
            'total_events': 0,
            'events_by_type': {},
            'events_by_source': {},
            'last_event_time': None
        }
