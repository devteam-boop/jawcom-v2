"""Manual Email Send idempotency (app/api/message_routes.py::send_email only).

Not used by Journey Engine, Execution Engine, WhatsApp, or webhook
processing — those are untouched by this module and do not import it.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_send_idempotency import EmailSendIdempotency

logger = logging.getLogger(__name__)

DEDUP_WINDOW_SECONDS = 60
DEFAULT_CLEANUP_AGE_DAYS = 30


def compute_dedup_key(
    lead_id: int,
    template_key: Optional[str],
    stage: str,
    module: str,
    context_id: Optional[str],
    subject: str,
    body: str,
) -> str:
    """Deterministic sha256 digest over the fields that define "the same
    manual email send": lead_id, template_key, stage, module, context_id,
    subject, body (rendered — the literal content Resend would receive).

    JSON-encoded as a list (not delimiter-joined) so field boundaries can
    never collide regardless of the field values themselves.
    """
    canonical = json.dumps(
        [
            lead_id,
            template_key or "",
            stage,
            module,
            context_id or "",
            subject,
            body,
        ],
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class IdempotencyResult:
    is_duplicate: bool
    communication_event_id: UUID
    provider_message_id: Optional[str]


async def check_and_reserve(
    session: AsyncSession,
    dedup_key: str,
    *,
    lead_id: int,
    template_key: Optional[str],
    request_id: str,
) -> IdempotencyResult:
    """Atomically reserve ``dedup_key`` for a new send, or detect that an
    equivalent request already reserved it within the last 60 seconds.

    Uses ``INSERT ... ON CONFLICT (dedup_key) DO UPDATE ... WHERE
    reserved_at < now() - 60s``: Postgres serializes concurrent inserts on
    the same conflicting key (a second concurrent call blocks on the first
    transaction's row lock until it commits), so two near-simultaneous
    retries can never both win the reservation — closing the race, not just
    reducing its window.

    - No existing row: the INSERT has no conflict, a row is written and
      returned by RETURNING -> IDEMPOTENCY_MISS.
    - An existing row older than 60s: the conflict's WHERE clause matches,
      the UPDATE reactivates that row (fresh reserved_at) and RETURNING
      yields it -> IDEMPOTENCY_EXPIRED. Same as MISS from the caller's
      perspective (proceed normally, not a duplicate) — logged separately
      only so a genuinely-new send is distinguishable from a reused key.
    - An existing row within 60s: the conflict's WHERE clause is false, so
      the UPDATE is a no-op and RETURNING yields nothing -> IDEMPOTENCY_HIT;
      the pre-existing row's communication_event_id/provider_message_id are
      then read back and returned instead.

    ``lead_id``/``template_key``/``request_id`` are logging-only — none of
    them participate in the dedup decision (``dedup_key`` already encodes
    everything that matters); they exist purely so IDEMPOTENCY_HIT/MISS/
    EXPIRED log lines are traceable back to one specific request.
    """
    started = time.perf_counter()
    now = datetime.utcnow()
    new_event_id = uuid4()

    # Best-effort classification only (MISS vs EXPIRED for logging) — the
    # UPSERT below is the sole source of truth for the actual HIT/MISS
    # decision, so a race between this read and the UPSERT (another
    # request reserving the same key in between) can at most mislabel one
    # log line, never affect correctness.
    pre_check = await session.execute(
        select(EmailSendIdempotency.id).where(EmailSendIdempotency.dedup_key == dedup_key)
    )
    had_existing_row = pre_check.first() is not None

    stmt = (
        pg_insert(EmailSendIdempotency)
        .values(
            id=uuid4(),
            dedup_key=dedup_key,
            communication_event_id=new_event_id,
            provider_message_id=None,
            reserved_at=now,
            created_at=now,
            updated_at=now,
        )
        .on_conflict_do_update(
            index_elements=["dedup_key"],
            set_={
                "communication_event_id": new_event_id,
                "provider_message_id": None,
                "reserved_at": now,
                "updated_at": now,
            },
            where=(EmailSendIdempotency.reserved_at < now - timedelta(seconds=DEDUP_WINDOW_SECONDS)),
        )
        .returning(EmailSendIdempotency.communication_event_id)
    )
    result = await session.execute(stmt)
    row = result.first()

    if row is not None:
        await session.commit()
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        tag = "IDEMPOTENCY_EXPIRED" if had_existing_row else "IDEMPOTENCY_MISS"
        logger.info(
            "%s dedup_key=%s lead_id=%s template_key=%s request_id=%s "
            "communication_event_id=%s processing_time_ms=%s",
            tag, dedup_key, lead_id, template_key, request_id, new_event_id, elapsed_ms,
        )
        return IdempotencyResult(is_duplicate=False, communication_event_id=new_event_id, provider_message_id=None)

    # Conflict existed and is still within the window — the reservation
    # attempt above made no changes, so roll back before reading (this
    # session issued no writes that need to survive).
    await session.rollback()
    existing = await session.execute(
        select(EmailSendIdempotency.communication_event_id, EmailSendIdempotency.provider_message_id)
        .where(EmailSendIdempotency.dedup_key == dedup_key)
    )
    existing_row = existing.first()
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        "IDEMPOTENCY_HIT dedup_key=%s lead_id=%s template_key=%s request_id=%s "
        "communication_event_id=%s provider_message_id=%s processing_time_ms=%s",
        dedup_key, lead_id, template_key, request_id,
        existing_row.communication_event_id if existing_row else None,
        existing_row.provider_message_id if existing_row else None,
        elapsed_ms,
    )
    return IdempotencyResult(
        is_duplicate=True,
        communication_event_id=existing_row.communication_event_id,
        provider_message_id=existing_row.provider_message_id if existing_row else None,
    )


async def cleanup_expired(session: AsyncSession, older_than_days: int = DEFAULT_CLEANUP_AGE_DAYS) -> int:
    """Delete email_send_idempotency rows whose reserved_at is older than
    ``older_than_days``. Touches only this table — communication_events
    (the durable send/audit log) is never referenced here, so this cleanup
    cannot affect it regardless of retention settings.

    Intended to be run periodically by an external scheduler (see
    scripts/cleanup_email_idempotency.py), not from any request path — the
    idempotency window itself is only 60 seconds, so a 30-day retention is
    pure operational housekeeping (bounding table growth), not a
    correctness requirement.
    """
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    result = await session.execute(
        delete(EmailSendIdempotency).where(EmailSendIdempotency.reserved_at < cutoff)
    )
    await session.commit()
    deleted_count = result.rowcount or 0
    logger.info(
        "Email idempotency cleanup: deleted %d row(s) with reserved_at older than %d days",
        deleted_count, older_than_days,
    )
    return deleted_count


async def record_provider_message_id(session: AsyncSession, dedup_key: str, provider_message_id: str) -> None:
    """Backfill the real Resend id once known, so a retry that arrives
    after the original send completed (but still within the 60s window)
    returns the real provider_message_id instead of None on its
    IDEMPOTENCY_HIT."""
    from sqlalchemy import update

    await session.execute(
        update(EmailSendIdempotency)
        .where(EmailSendIdempotency.dedup_key == dedup_key)
        .values(provider_message_id=provider_message_id)
    )
    await session.commit()
