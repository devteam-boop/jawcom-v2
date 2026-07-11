"""Periodic housekeeping: delete email_send_idempotency rows older than
30 days (default).

Manual Email Send idempotency only (see app/services/
email_idempotency_service.py, app/api/message_routes.py::send_email). The
idempotency window itself is 60 seconds — this script exists purely to
bound table growth over time, not for correctness. Touches only
email_send_idempotency; communication_events (the durable send/audit log)
is never read or written here.

Intended to run periodically via an external scheduler (e.g. a Render Cron
Job), not from the request path and not from any in-process scheduler —
does not touch Journey Engine, Execution Engine, WhatsApp, or webhook
processing.

Usage:
    python -m scripts.cleanup_email_idempotency
    python -m scripts.cleanup_email_idempotency --older-than-days 30

Run from backend/ with the same environment (.env / DATABASE_URL) as the
running app.
"""

import argparse
import asyncio
import logging

from app.database.session import async_session_maker
from app.services.email_idempotency_service import DEFAULT_CLEANUP_AGE_DAYS, cleanup_expired

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cleanup_email_idempotency")


async def run(older_than_days: int) -> int:
    async with async_session_maker() as session:
        return await cleanup_expired(session, older_than_days=older_than_days)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--older-than-days", type=int, default=DEFAULT_CLEANUP_AGE_DAYS,
        help=f"Delete rows with reserved_at older than this many days (default: {DEFAULT_CLEANUP_AGE_DAYS})",
    )
    args = parser.parse_args()

    deleted = asyncio.run(run(args.older_than_days))
    logger.info("Cleanup complete: deleted=%s (older_than_days=%s)", deleted, args.older_than_days)


if __name__ == "__main__":
    main()
