"""Base event classes and interfaces for the event system."""

from typing import Dict, Any, Optional, Type
from datetime import datetime
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(str, Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class BaseEvent(BaseModel, ABC):
    """
    Base class for all events in the system.
    
    Provides common event metadata and structure.
    All business events must inherit from this class.
    """
    
    # Event metadata
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., description="Type of event (e.g., 'lead.created')")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(..., description="Source system that generated the event")
    version: str = Field(default="1.0", description="Event schema version")
    
    # Processing metadata
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    
    # Event payload
    data: Dict[str, Any] = Field(..., description="Event-specific data payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Correlation and tracing
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @abstractmethod
    def get_event_key(self) -> str:
        """
        Get a unique key for this event type.
        Used for routing and handler registration.
        """
        pass
    
    @abstractmethod
    def validate_payload(self) -> bool:
        """
        Validate the event payload data.
        Returns True if valid, raises ValidationError if invalid.
        """
        pass
    
    def mark_processing(self) -> None:
        """Mark event as currently being processed."""
        self.status = EventStatus.PROCESSING
    
    def mark_completed(self) -> None:
        """Mark event as successfully processed."""
        self.status = EventStatus.COMPLETED
    
    def mark_failed(self, error: Optional[str] = None) -> None:
        """Mark event as failed processing."""
        self.status = EventStatus.FAILED
        if error:
            self.metadata["error"] = error
    
    def increment_retry(self) -> bool:
        """
        Increment retry count and update status.
        Returns True if retry is allowed, False if max retries exceeded.
        """
        self.retry_count += 1
        if self.retry_count <= self.max_retries:
            self.status = EventStatus.RETRYING
            return True
        else:
            self.mark_failed("Max retries exceeded")
            return False
    
    def should_retry(self) -> bool:
        """Check if event should be retried."""
        return (
            self.status in [EventStatus.FAILED, EventStatus.RETRYING] and
            self.retry_count < self.max_retries
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseEvent":
        """Create event instance from dictionary."""
        return cls(**data)


class EventHandler(ABC):
    """
    Abstract base class for event handlers.
    
    All event handlers must implement the handle method.
    """
    
    @abstractmethod
    async def handle(self, event: BaseEvent) -> bool:
        """
        Handle the given event.
        
        Args:
            event: The event to handle
            
        Returns:
            bool: True if handled successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def can_handle(self, event: BaseEvent) -> bool:
        """
        Check if this handler can process the given event.
        
        Args:
            event: The event to check
            
        Returns:
            bool: True if this handler can process the event
        """
        pass
    
    def get_handler_name(self) -> str:
        """Get the name of this handler."""
        return self.__class__.__name__


class EventResult(BaseModel):
    """Result of event processing."""
    
    success: bool
    event_id: str
    handler_name: Optional[str] = None
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
