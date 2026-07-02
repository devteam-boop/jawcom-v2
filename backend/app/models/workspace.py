from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class Workspace(Base, BaseModel):
    __tablename__ = 'workspaces'
    
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="workspace")
    journeys = relationship("Journey", back_populates="workspace")
    templates = relationship("Template", back_populates="workspace")
    campaigns = relationship("Campaign", back_populates="workspace")
    conversations = relationship("Conversation", back_populates="workspace")
