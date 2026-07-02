from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum

class ConversationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"

class Conversation(Base, BaseModel):
    __tablename__ = 'conversations'
    
    channel = Column(Enum(ConversationChannel), nullable=False)
    recipient_id = Column(String(255), nullable=False)  # External ID of the recipient
    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id'), nullable=False)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    running_instances = relationship("RunningJourneyInstance", back_populates="conversation")
