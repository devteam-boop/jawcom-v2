from sqlalchemy import Column, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel


class FlowVersion(Base, BaseModel):
    __tablename__ = 'flow_versions'

    flow_definition_id = Column(UUID(as_uuid=True), ForeignKey('flow_definitions.id'), nullable=False)
    version = Column(Integer, nullable=False)
    definition = Column(JSON, nullable=False)
    change_log = Column(Text)

    flow_definition = relationship("FlowDefinition", back_populates="versions")
