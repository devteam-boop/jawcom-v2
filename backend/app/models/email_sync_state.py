"""Gmail reply-sync cursor persistence.

Single small table, distinct from communication_events by design — this
tracks *sync execution state* (when did we last successfully poll Gmail),
not a communication event. Keyed by sync_name so a second named sync could
be added later without a schema change; today only "gmail_inbox" is used.
"""

from sqlalchemy import Column, DateTime, String

from .base import Base, BaseModel


class EmailSyncState(Base, BaseModel):
    __tablename__ = "email_sync_state"

    sync_name = Column(String(100), nullable=False, unique=True, index=True)
    last_synced_at = Column(DateTime, nullable=True)
