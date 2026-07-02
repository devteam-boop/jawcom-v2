from sqlalchemy import Column, String, Text, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum

class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Campaign(Base, BaseModel):
    __tablename__ = 'campaigns'
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id'), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey('templates.id'), nullable=False)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="campaigns")
    template = relationship("Template")
    recipients = relationship("CampaignRecipient", back_populates="campaign")
