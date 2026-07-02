from sqlalchemy import Column, String, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum

class InstanceStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"

class RunningJourneyInstance(Base, BaseModel):
    __tablename__ = 'running_journey_instances'
    
    status = Column(Enum(InstanceStatus), default=InstanceStatus.RUNNING, nullable=False)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime)
    current_stage_id = Column(UUID(as_uuid=True))  # Reference to current stage
    journey_id = Column(UUID(as_uuid=True), ForeignKey('journeys.id'), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
    
    # Relationships
    journey = relationship("Journey", back_populates="running_instances")
    conversation = relationship("Conversation", back_populates="running_instances")
