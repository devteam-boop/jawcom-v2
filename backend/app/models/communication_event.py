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

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, JSON, String, func
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
    # Inbound provider status updates (Meta WhatsApp Cloud API / Resend
    # webhooks). Channel-agnostic by design — the existing `channel` column
    # (whatsapp/email) already distinguishes which provider these came from,
    # so no per-channel variants (e.g. "whatsapp_delivered") were added.
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    FAILED = "failed"


class CommunicationEventChannel(str, enum.Enum):
    SYSTEM = "system"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class CommunicationEvent(Base, BaseModel):
    __tablename__ = "communication_events"

    running_instance_id = Column(
        UUID(as_uuid=True), ForeignKey("running_journey_instances.id"),
        nullable=False, index=True,
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
