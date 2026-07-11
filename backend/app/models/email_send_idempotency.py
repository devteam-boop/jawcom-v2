"""Manual Email Send idempotency (app/api/message_routes.py::send_email).

Closes the "JAWIS retries POST /api/messages/email/send on timeout -> two
real Resend sends" gap: a retried request with the same lead/template/
stage/module/context/subject/body within 60s must not call Resend again.

One row per ``dedup_key`` (unique). ``dedup_key`` is a sha256 digest of the
identifying fields (see app/services/email_idempotency_service.py) — not the
request body verbatim, so equivalent requests with different key ordering
still collide correctly and the raw payload is never duplicated here.

Reused/expired via ``INSERT ... ON CONFLICT (dedup_key) DO UPDATE ...
WHERE created_at < now() - 60s`` (see email_idempotency_service.py): a
dedup_key older than the 60s window is treated as a brand new request, not
a duplicate, so this table never blocks a genuinely new send that happens
to reuse the exact same content later.

Manual Email only — Journey Engine, Execution Engine, WhatsApp, and webhook
processing are untouched and do not read or write this table.
"""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, BaseModel


class EmailSendIdempotency(Base, BaseModel):
    __tablename__ = "email_send_idempotency"

    dedup_key = Column(String(64), nullable=False, unique=True, index=True)
    communication_event_id = Column(UUID(as_uuid=True), nullable=False)
    # NULL until the background send task (message_routes.py::
    # _send_email_and_record) learns the real id from Resend's response —
    # a fast retry landing before that happens returns None here, exactly
    # matching what the very first request's own synchronous 202 already
    # returns today (see EmailSendResponse), so this is not a behavior change.
    provider_message_id = Column(String(255), nullable=True)
    # Anchor for the 60s window — reset to now() on every reuse of an
    # expired dedup_key (see the ON CONFLICT ... DO UPDATE above), separate
    # from BaseModel.updated_at so query logic reads as self-explanatory.
    # Indexed (migration d9e0f1a2b3c4) for scripts/cleanup_email_idempotency.py's
    # by-age DELETE — the dedup_key unique index doesn't help that query.
    reserved_at = Column(DateTime, nullable=False, index=True)
