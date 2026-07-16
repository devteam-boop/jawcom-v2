"""Journey-driven Send idempotency (send_whatsapp_executor.py /
send_email_executor.py only).

Closes the "journey re-triggered / node retried -> the same send_whatsapp or
send_email step fires twice" gap: a webhook replay that creates a second
RunningJourneyInstance, or a manual node/journey retry that re-executes an
already-sent node, must not call JAWIS again for the same
(lead_id, node_id, template) within the dedup window.

One row per ``dedup_key`` (unique). ``dedup_key`` is a sha256 digest of the
identifying fields (see app/services/journey_send_idempotency_service.py) —
mirrors app/models/email_send_idempotency.py's proven pattern, kept as a
separate table since that one is explicitly scoped to the manual email send
API and not read by the Journey Engine.

Journey Engine sends only (WhatsApp + Email) — manual sends via
app/api/message_routes.py are untouched and do not read or write this table.
"""

from sqlalchemy import BigInteger, Column, DateTime, String

from .base import Base, BaseModel


class JourneySendIdempotency(Base, BaseModel):
    __tablename__ = "journey_send_idempotency"

    dedup_key = Column(String(64), nullable=False, unique=True, index=True)
    # Debugging/observability only — not part of the dedup decision
    # (dedup_key already encodes lead_id + node_id + template).
    lead_id = Column(BigInteger, nullable=False)
    node_id = Column(String(255), nullable=True)
    # Anchor for the dedup window — reset to now() on every reuse of an
    # expired dedup_key (see the ON CONFLICT ... DO UPDATE in the service).
    reserved_at = Column(DateTime, nullable=False, index=True)
