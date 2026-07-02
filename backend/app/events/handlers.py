"""Event handlers for processing business events."""

import logging
from typing import Optional
from datetime import datetime

from .base_event import BaseEvent, EventHandler
from .event_types import (
    LeadCreatedEvent,
    LeadStageChangedEvent,
    LeadAssignedEvent,
    LeadRequirementMetEvent
)

logger = logging.getLogger(__name__)


class CommunicationEventHandler(EventHandler):
    """
    Event handler that processes business events for communication triggers.
    
    This handler will eventually integrate with the Communication Engine
    to trigger journeys and send messages based on business events.
    """
    
    def __init__(self, communication_engine=None):
        """
        Initialize the communication event handler.
        
        Args:
            communication_engine: Optional CommunicationEngine instance
        """
        self.communication_engine = communication_engine
    
    async def handle(self, event: BaseEvent) -> bool:
        """
        Handle business events for communication triggers.
        
        Args:
            event: The business event to handle
            
        Returns:
            bool: True if handled successfully
        """
        try:
            logger.info(f"Processing {event.get_event_key()} event: {event.event_id}")
            
            if isinstance(event, LeadCreatedEvent):
                return await self._handle_lead_created(event)
            elif isinstance(event, LeadStageChangedEvent):
                return await self._handle_lead_stage_changed(event)
            elif isinstance(event, LeadAssignedEvent):
                return await self._handle_lead_assigned(event)
            elif isinstance(event, LeadRequirementMetEvent):
                return await self._handle_lead_requirement_met(event)
            else:
                logger.warning(f"Unknown event type: {event.get_event_key()}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling event {event.event_id}: {str(e)}")
            return False
    
    def can_handle(self, event: BaseEvent) -> bool:
        """
        Check if this handler can process the given event.
        
        Args:
            event: The event to check
            
        Returns:
            bool: True if this handler can process the event
        """
        supported_types = [
            LeadCreatedEvent,
            LeadStageChangedEvent,
            LeadAssignedEvent,
            LeadRequirementMetEvent
        ]
        return any(isinstance(event, event_type) for event_type in supported_types)
    
    async def _handle_lead_created(self, event: LeadCreatedEvent) -> bool:
        """
        Handle lead created events.
        
        In the future, this will:
        1. Check for stage mappings that trigger on lead creation
        2. Start appropriate journeys for the new lead
        3. Send welcome messages if configured
        
        Args:
            event: The lead created event
            
        Returns:
            bool: True if handled successfully
        """
        logger.info(f"Lead created: {event.lead_id} in stage {event.stage_key}")
        
        # TODO: Future implementation will:
        # 1. Query stage_mappings collection for mappings with trigger='lead.created'
        # 2. For each matching mapping, start a journey instance
        # 3. Use CommunicationEngine to send initial messages
        
        # For now, just log the event
        logger.info(f"Would trigger journeys for new lead {event.lead_id} in stage {event.stage_key}")
        
        return True
    
    async def _handle_lead_stage_changed(self, event: LeadStageChangedEvent) -> bool:
        """
        Handle lead stage changed events.
        
        In the future, this will:
        1. Check for stage mappings that trigger on the new stage
        2. Start appropriate journeys for the lead
        3. Stop any journeys that are no longer relevant
        
        Args:
            event: The lead stage changed event
            
        Returns:
            bool: True if handled successfully
        """
        logger.info(f"Lead {event.lead_id} moved from {event.from_stage_key} to {event.to_stage_key}")
        
        # TODO: Future implementation will:
        # 1. Query stage_mappings collection for mappings with stage_key=event.to_stage_key
        # 2. For each matching mapping, start a journey instance
        # 3. Optionally stop running instances for the previous stage
        # 4. Use CommunicationEngine to send stage-specific messages
        
        # For now, just log the event
        logger.info(f"Would trigger journeys for lead {event.lead_id} entering stage {event.to_stage_key}")
        
        return True
    
    async def _handle_lead_assigned(self, event: LeadAssignedEvent) -> bool:
        """
        Handle lead assigned events.
        
        In the future, this will:
        1. Send notification to the new assignee
        2. Update any running journey instances with new assignee context
        3. Trigger assignment-specific communication flows
        
        Args:
            event: The lead assigned event
            
        Returns:
            bool: True if handled successfully
        """
        logger.info(f"Lead {event.lead_id} assigned to {event.assigned_to}")
        
        # TODO: Future implementation will:
        # 1. Send notification message to new assignee
        # 2. Update running journey instances with assignee context
        # 3. Trigger any assignment-specific workflows
        
        # For now, just log the event
        logger.info(f"Would notify {event.assigned_to} about lead assignment {event.lead_id}")
        
        return True
    
    async def _handle_lead_requirement_met(self, event: LeadRequirementMetEvent) -> bool:
        """
        Handle lead requirement met events.
        
        In the future, this will:
        1. Check if requirement completion triggers any journeys
        2. Send congratulatory or next-step messages
        3. Update journey context with requirement data
        
        Args:
            event: The lead requirement met event
            
        Returns:
            bool: True if handled successfully
        """
        logger.info(f"Lead {event.lead_id} met requirement {event.requirement_key}")
        
        # TODO: Future implementation will:
        # 1. Check for journeys triggered by specific requirements
        # 2. Send requirement-specific messages
        # 3. Update journey context with requirement data
        
        # For now, just log the event
        logger.info(f"Would trigger requirement-based journeys for lead {event.lead_id}")
        
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
