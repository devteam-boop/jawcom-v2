from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class FlowDefinition(Base, BaseModel):
    __tablename__ = 'flow_definitions'
    
    definition = Column(Text, nullable=False)  # JSON definition of the flow
    journey_id = Column(UUID(as_uuid=True), ForeignKey('journeys.id'), nullable=False)
    
    # Relationships
    journey = relationship("Journey", back_populates="flow_definition")
