from sqlalchemy import Column, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
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
    # No Python-level ForeignKey/relationship to Workspace: the Workspace/
    # Campaign/Message cluster is a dormant, unregistered scaffold whose
    # module is never imported anywhere in the app (Journey doesn't even
    # declare the matching side of that relationship). Declaring
    # ForeignKey('workspaces.id') here would make SQLAlchemy require the
    # `workspaces` table to be present in Base.metadata at flush time, which
    # it isn't. The column stays nullable UUID; the physical DB-level FK
    # constraint (see migration f1a2b3c4d5e6) is left in place so workspace
    # scoping can be wired back up later with zero further schema changes.
    workspace_id = Column(UUID(as_uuid=True), nullable=True)
