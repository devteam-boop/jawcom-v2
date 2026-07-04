from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel


class StageMapping(Base, BaseModel):
    __tablename__ = 'stage_mappings'

    journey_id = Column(UUID(as_uuid=True), ForeignKey('journeys.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    stage_key = Column(String(255), nullable=False)
    template_id = Column(UUID(as_uuid=True))
    channel = Column(String(50))
    sort_order = Column(Integer, default=0)
    config = Column(JSON, default={})

    journey = relationship("Journey", back_populates="stage_mappings")
