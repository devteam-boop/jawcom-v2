from sqlalchemy import Column, String, Text, Enum, ForeignKey
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
    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id'), nullable=False)
    flow_definition_id = Column(UUID(as_uuid=True), ForeignKey('flow_definitions.id'), nullable=False)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="journeys")
    flow_definition = relationship("FlowDefinition", back_populates="journey")
    stage_mappings = relationship("StageMapping", back_populates="journey")
    running_instances = relationship("RunningJourneyInstance", back_populates="journey")
