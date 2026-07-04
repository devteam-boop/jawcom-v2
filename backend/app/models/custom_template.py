from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from .base import Base, BaseModel


class CustomTemplate(Base, BaseModel):
    __tablename__ = 'custom_templates'

    channel = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    subject = Column(Text)
    body = Column(Text, nullable=False)
    module = Column(Text, nullable=False)
