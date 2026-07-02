from sqlalchemy import Column, Text, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum

class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class Message(Base, BaseModel):
    __tablename__ = 'messages'
    
    content = Column(Text, nullable=False)
    direction = Column(Enum(MessageDirection), nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT, nullable=False)
    sent_at = Column(DateTime, default=func.now())
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey('templates.id'))
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    template = relationship("Template")
