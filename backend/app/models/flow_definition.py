from sqlalchemy import Column, String, Text, Enum, JSON, Integer
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum


class FlowDefinitionStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class FlowDefinition(Base, BaseModel):
    __tablename__ = 'flow_definitions'

    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(FlowDefinitionStatus), default=FlowDefinitionStatus.DRAFT, nullable=False)
    definition = Column(JSON, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    versions = relationship("FlowVersion", back_populates="flow_definition")
    execution_logs = relationship("FlowExecutionLog", back_populates="flow_definition")
