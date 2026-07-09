"""Gmail inbox reply-sync orchestration.

Flow per run:
  1. Load last_synced_at from email_sync_state (default: 24h lookback on
     first-ever run).
  2. List INBOX message ids received after that cursor (Gmail search is
     day-granular; precise filtering happens per-message via internalDate).
  3. For each message: extract headers/body, skip if already processed
     (idempotent by Gmail Message-ID — see CommunicationEventService.
     record_email_reply), match against a stored outbound rfc822_message_id
     or a previously-matched Gmail threadId, create an EMAIL_REPLIED
     CommunicationEvent if matched.
  4. Persist the new cursor (the time THIS run started, not ended — so a
     message that arrives mid-run is never skipped by the next run).

A message that errors during processing does not block the cursor from
advancing (it would otherwise infinitely reprocess one bad message every 5
minutes) — its id is returned in the result for visibility/manual follow-up.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.gmail_sync.client import GmailClient, GmailNotConfiguredError, extract_body, extract_headers, extract_references
from app.models.email_sync_state import EmailSyncState
from app.services.communication_event_service import CommunicationEventService

logger = logging.getLogger(__name__)

SYNC_NAME = "gmail_inbox"
DEFAULT_LOOKBACK = timedelta(hours=24)


class EmailSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gmail = GmailClient()
        self.events = CommunicationEventService(db)

    async def _get_last_synced_at(self) -> Optional[datetime]:
        result = await self.db.execute(
            select(EmailSyncState).where(EmailSyncState.sync_name == SYNC_NAME)
        )
        state = result.scalar_one_or_none()
        return state.last_synced_at if state else None

    async def _set_last_synced_at(self, when: datetime) -> None:
        result = await self.db.execute(
            select(EmailSyncState).where(EmailSyncState.sync_name == SYNC_NAME)
        )
        state = result.scalar_one_or_none()
        if state is None:
            state = EmailSyncState(id=uuid4(), sync_name=SYNC_NAME, last_synced_at=when)
            self.db.add(state)
        else:
            state.last_synced_at = when
        await self.db.commit()

    async def run(self) -> Dict[str, Any]:
        if not self.gmail.is_configured():
            return {
                "success": False,
                "error": "Gmail not configured (missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET/GOOGLE_REFRESH_TOKEN)",
            }

        last_synced_at = await self._get_last_synced_at()
        window_start = last_synced_at or (datetime.utcnow() - DEFAULT_LOOKBACK)
        run_started_at = datetime.utcnow()

        try:
            message_ids = await self.gmail.list_inbox_message_ids(after=window_start)
        except GmailNotConfiguredError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception("email_sync: failed to list INBOX messages")
            return {"success": False, "error": f"Gmail list failed: {exc}"}

        processed = 0
        matched = 0
        skipped_duplicate = 0
        skipped_old = 0
        unmatched = 0
        errors = []
        matched_details = []

        for message_id in message_ids:
            try:
                message = await self.gmail.get_message(message_id)

                internal_ms = int(message.get("internalDate") or 0)
                received_at = (
                    datetime.utcfromtimestamp(internal_ms / 1000) if internal_ms else None
                )
                if received_at is not None and received_at <= window_start:
                    skipped_old += 1
                    continue

                headers = extract_headers(message)
                gmail_message_id = headers.get("Message-ID") or headers.get("Message-Id") or message_id
                in_reply_to = headers.get("In-Reply-To")
                references = extract_references(headers)
                subject = headers.get("Subject", "")
                from_address = headers.get("From", "")
                thread_id = message.get("threadId", "")
                body = extract_body(message)

                processed += 1

                if await self.events.repo.exists_replied_by_gmail_message_id(gmail_message_id):
                    skipped_duplicate += 1
                    continue

                event = await self.events.record_email_reply(
                    gmail_message_id=gmail_message_id,
                    gmail_thread_id=thread_id,
                    in_reply_to=in_reply_to,
                    references=references,
                    subject=subject,
                    body=body,
                    from_address=from_address,
                    received_at=received_at,
                )

                if event:
                    matched += 1
                    matched_details.append({
                        "lead_id": event.lead_id,
                        "communication_event_id": event.id,
                        "gmail_message_id": gmail_message_id,
                        "subject": subject,
                        "from": from_address,
                    })
                else:
                    unmatched += 1
            except Exception as exc:
                logger.exception("email_sync: failed to process gmail message_id=%s", message_id)
                errors.append({"gmail_message_id": message_id, "error": str(exc)})

        await self._set_last_synced_at(run_started_at)

        return {
            "success": True,
            "window_start": window_start.isoformat(),
            "run_started_at": run_started_at.isoformat(),
            "messages_seen": len(message_ids),
            "processed": processed,
            "matched": matched,
            "skipped_duplicate": skipped_duplicate,
            "skipped_old": skipped_old,
            "unmatched": unmatched,
            "matched_details": matched_details,
            "errors": errors,
        }
