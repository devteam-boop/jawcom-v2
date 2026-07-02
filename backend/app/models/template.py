from sqlalchemy import Column, String, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum

class TemplateChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"

class TemplateStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"

class Template(Base, BaseModel):
    __tablename__ = 'templates'
    
    name = Column(String(255), nullable=False)
    subject = Column(String(255))  # For email templates
    content = Column(Text, nullable=False)
    channel = Column(Enum(TemplateChannel), nullable=False)
    status = Column(Enum(TemplateStatus), default=TemplateStatus.DRAFT, nullable=False)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id'), nullable=False)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="templates")
