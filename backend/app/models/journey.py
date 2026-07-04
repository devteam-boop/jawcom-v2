from sqlalchemy import Column, String, Text, Enum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum


class JourneyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Journey(Base, BaseModel):
    __tablename__ = 'journeys'

    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(JourneyStatus), default=JourneyStatus.DRAFT, nullable=False)
    trigger_type = Column(String(50), nullable=False)
    trigger_value = Column(String(255))
    flow_definition_id = Column(UUID(as_uuid=True), ForeignKey('flow_definitions.id'), nullable=True)
    config = Column(JSON, default={})

    stage_mappings = relationship("StageMapping", back_populates="journey")
    running_instances = relationship("RunningJourneyInstance", back_populates="journey")
    flow_definition = relationship("FlowDefinition", foreign_keys=[flow_definition_id])
