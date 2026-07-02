"""Event dispatcher for routing and processing events."""

from typing import Dict, List, Callable, Any, Optional
import asyncio
import logging
from datetime import datetime
from collections import defaultdict

from .base_event import BaseEvent, EventHandler, EventResult, EventStatus
from .event_types import create_event_from_type

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Central event dispatcher that routes events to registered handlers.
    
    Supports:
    - Handler registration by event type
    - Async event processing
    - Event queuing and batching
    - Retry logic for failed events
    - Event logging and metrics
    """
    
    def __init__(self):
        """Initialize the event dispatcher."""
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._event_queue: List[BaseEvent] = []
        self._processing = False
        self._metrics = {
            'events_processed': 0,
            'events_failed': 0,
            'events_retried': 0,
            'handlers_registered': 0
        }
    
    def register_handler(self, event_type: str, handler: EventHandler) -> None:
        """
        Register an event handler for a specific event type.
        
        Args:
            event_type: The event type to handle (e.g., 'lead.created')
            handler: The handler instance
        """
        self._handlers[event_type].append(handler)
        self._metrics['handlers_registered'] += 1
        logger.info(f"Registered handler {handler.get_handler_name()} for event type: {event_type}")
    
    def unregister_handler(self, event_type: str, handler: EventHandler) -> None:
        """
        Unregister an event handler.
        
        Args:
            event_type: The event type
            handler: The handler instance to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self._metrics['handlers_registered'] -= 1
                logger.info(f"Unregistered handler {handler.get_handler_name()} for event type: {event_type}")
            except ValueError:
                logger.warning(f"Handler {handler.get_handler_name()} not found for event type: {event_type}")
    
    def get_handlers(self, event_type: str) -> List[EventHandler]:
        """
        Get all handlers registered for an event type.
        
        Args:
            event_type: The event type
            
        Returns:
            List of handlers for the event type
        """
        return self._handlers.get(event_type, [])
    
    async def dispatch(self, event: BaseEvent) -> List[EventResult]:
        """
        Dispatch an event to all registered handlers.
        
        Args:
            event: The event to dispatch
            
        Returns:
            List of EventResult from all handlers
        """
        start_time = datetime.utcnow()
        results = []
        
        # Validate event
        try:
            event.validate_payload()
        except Exception as e:
            logger.error(f"Event validation failed: {str(e)}")
            event.mark_failed(f"Validation error: {str(e)}")
            return [EventResult(
                success=False,
                event_id=event.event_id,
                error=f"Validation error: {str(e)}"
            )]
        
        # Get handlers for this event type
        handlers = self.get_handlers(event.get_event_key())
        
        if not handlers:
            logger.warning(f"No handlers registered for event type: {event.get_event_key()}")
            return [EventResult(
                success=False,
                event_id=event.event_id,
                error=f"No handlers registered for event type: {event.get_event_key()}"
            )]
        
        # Mark event as processing
        event.mark_processing()
        
        # Process event with each handler
        for handler in handlers:
            handler_start = datetime.utcnow()
            
            try:
                if not handler.can_handle(event):
                    logger.debug(f"Handler {handler.get_handler_name()} cannot handle event {event.event_id}")
                    continue
                
                logger.info(f"Processing event {event.event_id} with handler {handler.get_handler_name()}")
                success = await handler.handle(event)
                
                processing_time = int((datetime.utcnow() - handler_start).total_seconds() * 1000)
                
                if success:
                    results.append(EventResult(
                        success=True,
                        event_id=event.event_id,
                        handler_name=handler.get_handler_name(),
                        processing_time_ms=processing_time
                    ))
                    logger.info(f"Handler {handler.get_handler_name()} successfully processed event {event.event_id}")
                else:
                    results.append(EventResult(
                        success=False,
                        event_id=event.event_id,
                        handler_name=handler.get_handler_name(),
                        processing_time_ms=processing_time,
                        error="Handler returned False"
                    ))
                    logger.warning(f"Handler {handler.get_handler_name()} failed to process event {event.event_id}")
                
            except Exception as e:
                processing_time = int((datetime.utcnow() - handler_start).total_seconds() * 1000)
                error_msg = f"Handler exception: {str(e)}"
                
                results.append(EventResult(
                    success=False,
                    event_id=event.event_id,
                    handler_name=handler.get_handler_name(),
                    processing_time_ms=processing_time,
                    error=error_msg
                ))
                
                logger.error(f"Handler {handler.get_handler_name()} threw exception for event {event.event_id}: {str(e)}")
        
        # Update event status based on results
        successful_results = [r for r in results if r.success]
        if successful_results:
            event.mark_completed()
            self._metrics['events_processed'] += 1
        else:
            if event.increment_retry():
                self._metrics['events_retried'] += 1
                logger.info(f"Event {event.event_id} will be retried (attempt {event.retry_count})")
            else:
                self._metrics['events_failed'] += 1
                logger.error(f"Event {event.event_id} failed after {event.retry_count} attempts")
        
        total_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.info(f"Event {event.event_id} processing completed in {total_time}ms")
        
        return results
    
    async def dispatch_from_dict(self, event_data: Dict[str, Any]) -> List[EventResult]:
        """
        Create and dispatch an event from dictionary data.
        
        Args:
            event_data: Dictionary containing event data
            
        Returns:
            List of EventResult from all handlers
        """
        try:
            event_type = event_data.get('event_type')
            if not event_type:
                raise ValueError("Missing event_type in event data")
            
            event = create_event_from_type(event_type, **event_data)
            return await self.dispatch(event)
            
        except Exception as e:
            logger.error(f"Failed to create event from dict: {str(e)}")
            return [EventResult(
                success=False,
                event_id=event_data.get('event_id', 'unknown'),
                error=f"Event creation error: {str(e)}"
            )]
    
    def queue_event(self, event: BaseEvent) -> None:
        """
        Add an event to the processing queue.
        
        Args:
            event: The event to queue
        """
        self._event_queue.append(event)
        logger.debug(f"Queued event {event.event_id} of type {event.get_event_key()}")
    
    async def process_queue(self) -> List[EventResult]:
        """
        Process all events in the queue.
        
        Returns:
            List of all EventResult from queue processing
        """
        if self._processing:
            logger.warning("Queue processing already in progress")
            return []
        
        self._processing = True
        all_results = []
        
        try:
            while self._event_queue:
                event = self._event_queue.pop(0)
                results = await self.dispatch(event)
                all_results.extend(results)
                
                # Handle retry logic
                if event.should_retry():
                    self._event_queue.append(event)
                    logger.info(f"Re-queued event {event.event_id} for retry")
        
        finally:
            self._processing = False
        
        return all_results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get dispatcher metrics."""
        return {
            **self._metrics,
            'queue_size': len(self._event_queue),
            'registered_event_types': list(self._handlers.keys()),
            'total_handlers': sum(len(handlers) for handlers in self._handlers.values())
        }
    
    def clear_queue(self) -> int:
        """
        Clear the event queue.
        
        Returns:
            Number of events that were cleared
        """
        count = len(self._event_queue)
        self._event_queue.clear()
        logger.info(f"Cleared {count} events from queue")
        return count


# Global dispatcher instance
_global_dispatcher: Optional[EventDispatcher] = None


def get_dispatcher() -> EventDispatcher:
    """Get the global event dispatcher instance."""
    global _global_dispatcher
    if _global_dispatcher is None:
        _global_dispatcher = EventDispatcher()
    return _global_dispatcher


def reset_dispatcher() -> None:
    """Reset the global dispatcher (mainly for testing)."""
    global _global_dispatcher
    _global_dispatcher = None
