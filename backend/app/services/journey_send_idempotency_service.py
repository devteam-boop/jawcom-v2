"""Journey-driven Send idempotency (send_whatsapp_executor.py /
send_email_executor.py only).

Enforces "one journey step = one send": a webhook replay that spins up a
second RunningJourneyInstance, or a node/journey retry that re-executes an
already-sent node, must not call JAWIS again for the same
(lead_id, node_id, template) within DEDUP_WINDOW_SECONDS.

Same atomic-reservation strategy as
app/services/email_idempotency_service.py (INSERT ... ON CONFLICT
(dedup_key) DO UPDATE ... WHERE reserved_at < now() - window): Postgres
serializes concurrent inserts on the same conflicting key, so two
near-simultaneous re-executions can never both win the reservation. Kept as
a separate function/table rather than reusing that module because this one
has no HTTP caller to backfill a provider_message_id for — the decision
here is a plain "have I reserved this key recently?" boolean.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journey_send_idempotency import JourneySendIdempotency

logger = logging.getLogger(__name__)

DEDUP_WINDOW_SECONDS = 60


def compute_dedup_key(lead_id: int, node_id: Optional[str], template: Optional[str]) -> str:
    """Deterministic sha256 digest over (lead_id, node_id, template) — the
    fields that define "the same journey-step send". JSON-encoded as a list
    (not delimiter-joined) so field boundaries can never collide regardless
    of the field values themselves — same convention as
    email_idempotency_service.compute_dedup_key().
    """
    canonical = json.dumps(
        [lead_id, node_id or "", template or ""],
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def check_and_reserve(
    session: AsyncSession,
    dedup_key: str,
    *,
    lead_id: int,
    node_id: Optional[str],
) -> bool:
    """Atomically reserve ``dedup_key`` for a new send, or detect that this
    exact journey step already reserved it within the last
    ``DEDUP_WINDOW_SECONDS``.

    Returns ``True`` when this call is a duplicate (an equivalent send was
    already reserved/sent within the window — the caller must skip the
    actual provider call) and ``False`` when this call just won the
    reservation and should proceed with the send.
    """
    now = datetime.utcnow()

    stmt = (
        pg_insert(JourneySendIdempotency)
        .values(
            id=uuid4(),
            dedup_key=dedup_key,
            lead_id=lead_id,
            node_id=node_id,
            reserved_at=now,
            created_at=now,
            updated_at=now,
        )
        .on_conflict_do_update(
            index_elements=["dedup_key"],
            set_={"reserved_at": now, "updated_at": now},
            where=(JourneySendIdempotency.reserved_at < now - timedelta(seconds=DEDUP_WINDOW_SECONDS)),
        )
        .returning(JourneySendIdempotency.id)
    )
    result = await session.execute(stmt)
    row = result.first()

    if row is not None:
        await session.commit()
        logger.info(
            "JOURNEY_SEND_IDEMPOTENCY_MISS dedup_key=%s lead_id=%s node_id=%s",
            dedup_key, lead_id, node_id,
        )
        return False

    # Conflict existed and is still within the window — the reservation
    # attempt above made no changes, so roll back before returning (this
    # session issued no writes that need to survive).
    await session.rollback()
    logger.info(
        "JOURNEY_SEND_IDEMPOTENCY_HIT dedup_key=%s lead_id=%s node_id=%s — skipping duplicate send",
        dedup_key, lead_id, node_id,
    )
    return True
