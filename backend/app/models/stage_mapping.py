from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class StageMapping(Base, BaseModel):
    __tablename__ = 'stage_mappings'
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    journey_id = Column(UUID(as_uuid=True), ForeignKey('journeys.id'), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey('templates.id'))
    
    # Relationships
    journey = relationship("Journey", back_populates="stage_mappings")
    template = relationship("Template")
