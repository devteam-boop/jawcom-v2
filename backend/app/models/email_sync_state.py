"""Gmail reply-sync cursor persistence.

Single small table, distinct from communication_events by design — this
tracks *sync execution state* (when did we last successfully poll Gmail),
not a communication event. Keyed by sync_name so a second named sync could
be added later without a schema change; "gmail_inbox" (Gmail sync) and
"whatsapp_templates" (WhatsApp Template Management's Meta sync, see
app/whatsapp_templates/service.py) both use this table today.
"""

from sqlalchemy import Column, DateTime, String, Text

from .base import Base, BaseModel


class EmailSyncState(Base, BaseModel):
    __tablename__ = "email_sync_state"

    sync_name = Column(String(100), nullable=False, unique=True, index=True)
    last_synced_at = Column(DateTime, nullable=True)
    # Set when the last attempt for this sync_name failed (cleared on the
    # next success) — operational visibility for "Sync Status" (WhatsApp
    # Template Management Phase 7). NULL for Gmail sync, which doesn't use
    # this field.
    last_error = Column(Text, nullable=True)
