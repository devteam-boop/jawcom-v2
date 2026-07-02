from sqlalchemy import Column, String, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum

class RecipientStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

class CampaignRecipient(Base, BaseModel):
    __tablename__ = 'campaign_recipients'
    
    recipient_id = Column(String(255), nullable=False)  # External ID of the recipient
    status = Column(Enum(RecipientStatus), default=RecipientStatus.PENDING, nullable=False)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id'), nullable=False)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="recipients")
