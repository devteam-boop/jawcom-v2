from sqlalchemy import Column, String, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class User(Base, BaseModel):
    __tablename__ = 'users'
    
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    workspace_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="users")
