"""Canonical Communication Event model.

Append-only log of every communication-relevant action a journey takes
(journey start, node execution, message send, task lifecycle, ...).

Distinct from ``FlowExecutionLog`` (app/models/flow_execution_log.py), which
is an internal node-execution debug trail (one "started" + one
"success"/"failed"/"skipped" row per node, keyed by node_id/status). This
model is the domain-level event stream a future Communication Timeline /
Inbox reads from — one row per meaningful action, keyed by event_type.

``provider``/``provider_message_id`` are included now (nullable, unused)
so that a future Meta Cloud API / Resend delivery-status webhook can update
or correlate against these rows via a stable message id, without a further
schema change.
"""

import enum

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, JSON, String, func, text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, BaseModel


class CommunicationEventType(str, enum.Enum):
    JOURNEY_STARTED = "journey_started"
    TRIGGER_EXECUTED = "trigger_executed"
    CONDITION_EVALUATED = "condition_evaluated"
    WAIT_STARTED = "wait_started"
    WAIT_COMPLETED = "wait_completed"
    WHATSAPP_SENT = "whatsapp_sent"
    EMAIL_SENT = "email_sent"
    NOTE_ADDED = "note_added"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    NOTIFICATION_SENT = "notification_sent"
    # Inbound provider status updates (Meta WhatsApp Cloud API / Resend
    # webhooks). Channel-agnostic by design — the existing `channel` column
    # (whatsapp/email) already distinguishes which provider these came from,
    # so no per-channel variants (e.g. "whatsapp_delivered") were added.
    DELIVERED = "delivered"
    READ = "read"
    CLICKED = "clicked"
    REPLIED = "replied"
    # FAILED = the *outbound send itself* failed (e.g. Resend API error,
    # provider misconfigured) — no provider_message_id exists yet, recorded
    # directly by the send endpoint, not via a webhook.
    FAILED = "failed"
    # BOUNCED/COMPLAINED = distinct webhook-sourced delivery outcomes,
    # previously folded into FAILED; split out so a bounce/spam-complaint
    # is distinguishable from an outbound send failure in the timeline.
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class CommunicationEventChannel(str, enum.Enum):
    SYSTEM = "system"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class CommunicationEvent(Base, BaseModel):
    __tablename__ = "communication_events"

    # Nullable: NULL = manual/general send (no Journey instance); a real
    # UUID = Journey-originated send. Manual and Journey communication share
    # this one table — see migration b4c5d6e7f8a9.
    running_instance_id = Column(
        UUID(as_uuid=True), ForeignKey("running_journey_instances.id"),
        nullable=True, index=True,
    )
    journey_id = Column(
        UUID(as_uuid=True), ForeignKey("journeys.id"), nullable=True, index=True,
    )
    lead_id = Column(BigInteger, nullable=False, index=True)
    node_id = Column(String(255), nullable=True)
    # Plain strings (not a DB enum) — matches FlowExecutionLog.status's
    # convention, and avoids an ALTER TYPE migration every time a future
    # sprint adds a new event type (delivered/read/replied, etc.).
    event_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), default=CommunicationEventChannel.SYSTEM.value, nullable=False)
    provider = Column(String(50), nullable=True)
    provider_message_id = Column(String(255), nullable=True, index=True)
    payload = Column(JSON, default={})
    occurred_at = Column(DateTime, default=func.now(), nullable=False)
    # Set when _publish_to_jawis (communication_event_service.py) gets a 2xx
    # from JAWIS_WEBHOOK_URL for this row; NULL means JAWIS has no confirmed
    # copy yet (never attempted, still retrying, or exhausted retries) — the
    # queryable set the backfill script targets. See migration e4f5a6b7c8d9.
    jawis_synced_at = Column(DateTime, nullable=True)

    # Webhook retries must never create duplicate rows (NULL provider_message_id
    # rows — internal/outbound-failure events — are exempt: SQL NULLs are never
    # considered equal to each other, so this only constrains provider-sourced
    # webhook events). See migration c1d2e3f4a5b7.
    #
    # Excludes event_type='replied': unlike delivered/opened/bounced (which
    # can only legitimately happen once per outbound message), a single
    # thread can receive multiple genuine separate replies, all correlated
    # to the same provider_message_id anchor. Reply-specific idempotency is
    # enforced at the application level instead, keyed on the inbound
    # Gmail message's own Message-ID (see app/gmail_sync/service.py).
    # See migration d2e3f4a5b6c8.
    __table_args__ = (
        Index(
            "uq_communication_events_pmid_event_type",
            "provider_message_id", "event_type",
            unique=True,
            postgresql_where=text("event_type != 'replied'"),
        ),
    )
