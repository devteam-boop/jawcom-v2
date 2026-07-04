from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime, func, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel


class FlowExecutionLog(Base, BaseModel):
    __tablename__ = 'flow_execution_logs'

    flow_definition_id = Column(UUID(as_uuid=True), ForeignKey('flow_definitions.id'), nullable=False)
    flow_version_id = Column(UUID(as_uuid=True), ForeignKey('flow_versions.id'))
    running_instance_id = Column(UUID(as_uuid=True), ForeignKey('running_journey_instances.id'), nullable=False)
    lead_id = Column(BigInteger, nullable=False, index=True)
    node_id = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    input = Column(JSON, default={})
    output = Column(JSON, default={})
    error_message = Column(Text)
    executed_at = Column(DateTime, default=func.now(), nullable=False)

    flow_definition = relationship("FlowDefinition", back_populates="execution_logs")
    flow_version = relationship("FlowVersion")
