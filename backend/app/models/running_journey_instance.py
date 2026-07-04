from sqlalchemy import Column, Enum, ForeignKey, DateTime, func, JSON, BigInteger
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

    lead_id = Column(BigInteger, nullable=False, index=True)
    journey_id = Column(UUID(as_uuid=True), ForeignKey('journeys.id'), nullable=False)
    current_stage_mapping_id = Column(UUID(as_uuid=True), ForeignKey('stage_mappings.id'))
    status = Column(Enum(InstanceStatus), default=InstanceStatus.RUNNING, nullable=False)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime)
    data = Column(JSON, default={})

    journey = relationship("Journey", back_populates="running_instances")
    current_stage_mapping = relationship("StageMapping")
