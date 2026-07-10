"""One-time, idempotent backfill: re-publish communication_events rows JAWIS
never confirmed receipt of.

Targets rows where jawis_synced_at IS NULL (see migration e4f5a6b7c8d9),
restricted to the event_types _publish_to_jawis actually sends
(app.services.communication_event_service._JAWIS_WEBHOOK_EVENT_TYPES).
Reuses _publish_to_jawis directly — same payload builder, same retry/backoff
as normal operation — so there is no separate serialization logic to drift
out of sync. On a confirmed 2xx it sets jawis_synced_at itself (same code
path as a live send), which is what makes re-running this script safe: a
second run only ever touches rows still NULL.

Idempotency note: JAWIS is expected to dedupe on event_id, so re-POSTing an
event that already made it through is expected to be a safe no-op 2xx on
JAWIS's side (recorded here as "synced", indistinguishable from — and
equivalent in effect to — a genuine first-time sync). There is deliberately
no separate "skipped" bucket in the summary: rows already marked
jawis_synced_at are excluded by the query before scanning even starts, and a
JAWIS-side idempotent no-op is not distinguishable from a first-time success
from JawCom's side, so both are counted as "synced".

IMPORTANT — first run: jawis_synced_at is NULL on every pre-existing row
(the column didn't exist before), not just genuinely-failed ones. The first
invocation will therefore attempt to (re-)publish every historical row
matching the event-type filter and date range, including ones JAWIS already
received before this column existed. That's expected and safe only because
JAWIS is expected to dedupe on event_id — confirm that before running this
at scale. Use --since/--until to scope the first run to a small, recent
window (e.g. today, one lead) rather than the full table.

Usage:
    python -m scripts.backfill_jawis_sync --since 2026-07-10 --lead-id 58
    python -m scripts.backfill_jawis_sync --since 2026-07-01 --until 2026-07-10
    python -m scripts.backfill_jawis_sync   # no bounds: every unsynced row

Run from backend/ with the same environment (.env / DATABASE_URL,
JAWIS_WEBHOOK_URL) as the running app. This script only reads
communication_events and (via _publish_to_jawis) sets jawis_synced_at on
success — it does not touch Journey Engine, Execution Engine, Template
Engine, or the Provider Layer.
"""

import argparse
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from app.config.settings import get_settings
from app.database.session import async_session_maker
from app.repositories.communication_event_repository import CommunicationEventRepository
from app.services.communication_event_service import (
    _JAWIS_WEBHOOK_EVENT_TYPES,
    _publish_to_jawis,
    CommunicationEventService,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("backfill_jawis_sync")

_BATCH_SIZE = 100


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


async def run(
    since: Optional[datetime],
    until: Optional[datetime],
    lead_id: Optional[int],
    max_events: Optional[int],
) -> Tuple[int, int, int, List[Tuple[str, str]]]:
    settings = get_settings()
    if not settings.JAWIS_WEBHOOK_URL:
        logger.error(
            "JAWIS_WEBHOOK_URL is not configured in this environment — "
            "refusing to run (there is nothing to resync against)."
        )
        return 0, 0, 0, []

    scanned = 0
    synced = 0
    failed = 0
    failures: List[Tuple[str, str]] = []

    async with async_session_maker() as session:
        repo = CommunicationEventRepository(session)
        service = CommunicationEventService(session)

        while max_events is None or scanned < max_events:
            batch_limit = _BATCH_SIZE if max_events is None else min(_BATCH_SIZE, max_events - scanned)
            batch = await repo.get_unsynced(
                event_types=_JAWIS_WEBHOOK_EVENT_TYPES,
                since=since,
                until=until,
                limit=batch_limit,
            )
            if not batch:
                break

            for event in batch:
                if lead_id is not None and event.lead_id != lead_id:
                    continue
                scanned += 1
                schema = service._to_schema(event)
                ok = await _publish_to_jawis(schema)
                if ok:
                    synced += 1
                else:
                    failed += 1
                    failures.append((str(event.id), event.event_type))

            if len(batch) < batch_limit:
                break

    return scanned, synced, failed, failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--since", help="ISO date/datetime lower bound on occurred_at, e.g. 2026-07-10")
    parser.add_argument("--until", help="ISO date/datetime upper bound on occurred_at, e.g. 2026-07-10")
    parser.add_argument("--lead-id", type=int, default=None, help="Restrict to a single lead_id (applied after the DB query)")
    parser.add_argument("--limit", type=int, default=None, help="Stop after attempting at most this many events")
    args = parser.parse_args()

    since = _parse_date(args.since)
    until = _parse_date(args.until)

    scanned, synced, failed, failures = asyncio.run(run(since, until, args.lead_id, args.limit))

    logger.info(
        "Backfill complete: scanned=%s synced=%s failed=%s (skipped=0 — already-synced rows are excluded "
        "by the query before scanning, not counted here)",
        scanned, synced, failed,
    )
    if failures:
        logger.info(
            "Still unsynced after this run (%s) — will be retried on the next invocation: %s",
            len(failures), failures[:50],
        )


if __name__ == "__main__":
    main()
