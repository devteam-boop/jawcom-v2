"""Manual/cron trigger for the Gmail reply-sync.

POST /api/email-sync/run — runs one sync cycle synchronously and returns
the result. Auth: X-Webhook-Token header, validated against
EMAIL_SYNC_WEBHOOK_TOKEN (same pattern as JAWIS's own _check_auth /
WEBHOOK_TOKEN, which this endpoint replaces). An external cron (GitHub
Actions, Render Cron Job, or any scheduler) calls this every 5 minutes —
no in-process scheduler is added here.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.dependencies import get_db_session
from app.gmail_sync.service import EmailSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email-sync", tags=["Email Sync"])


def _check_auth(x_webhook_token: Optional[str]) -> None:
    settings = get_settings()
    expected = settings.EMAIL_SYNC_WEBHOOK_TOKEN
    if not expected:
        logger.error("EMAIL_SYNC_WEBHOOK_TOKEN is not configured — refusing all requests")
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not x_webhook_token or x_webhook_token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/run")
async def run_email_sync(
    x_webhook_token: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db_session),
):
    _check_auth(x_webhook_token)
    service = EmailSyncService(db)
    result = await service.run()
    logger.info("email_sync run result: %s", result)
    return result
