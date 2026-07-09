"""Gmail API client — read-only INBOX access for reply tracking.

Credentials verified live before this module was written: the existing
GOOGLE_REFRESH_TOKEN successfully authenticates as GMAIL_MONITOR_EMAIL and
can list/read INBOX messages (google-api-python-client / google-auth were
already installed in this environment, just unused by any app code).

googleapiclient is a synchronous library (no native asyncio support) — all
blocking calls are run via asyncio.to_thread() so they don't block the
FastAPI event loop.
"""

import asyncio
import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_TOKEN_URI = "https://oauth2.googleapis.com/token"


class GmailNotConfiguredError(Exception):
    """Raised when Gmail OAuth credentials are missing."""


class GmailClient:
    """Thin wrapper around the Gmail API for INBOX polling."""

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.refresh_token = settings.GOOGLE_REFRESH_TOKEN
        self.monitor_email = settings.GMAIL_MONITOR_EMAIL
        self._service = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    def _build_service(self):
        if not self.is_configured():
            raise GmailNotConfiguredError(
                "Gmail not configured (missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET/GOOGLE_REFRESH_TOKEN)"
            )
        creds = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_uri=_TOKEN_URI,
        )
        creds.refresh(Request())
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def _get_service(self):
        if self._service is None:
            self._service = self._build_service()
        return self._service

    async def list_inbox_message_ids(self, after: datetime) -> List[str]:
        """Message IDs in INBOX from Gmail's `after:` search.

        Gmail's after:/before: search operators are DAY-granularity only —
        they cannot filter to the minute/second. To avoid missing messages
        near a sync boundary, this queries from one day before `after` and
        relies on the caller to filter precisely using each message's own
        internalDate (millisecond-precision, always present).
        """
        query_date = (after - timedelta(days=1)).strftime("%Y/%m/%d")
        query = f"in:inbox after:{query_date}"

        def _list_all() -> List[str]:
            service = self._get_service()
            ids: List[str] = []
            page_token = None
            while True:
                resp = service.users().messages().list(
                    userId="me", q=query, pageToken=page_token, maxResults=100,
                ).execute()
                ids.extend(m["id"] for m in resp.get("messages", []))
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break
            return ids

        return await asyncio.to_thread(_list_all)

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Full Gmail message resource (headers + body) for one message id."""

        def _get() -> Dict[str, Any]:
            service = self._get_service()
            return service.users().messages().get(
                userId="me", id=message_id, format="full",
            ).execute()

        return await asyncio.to_thread(_get)


def extract_headers(message: Dict[str, Any]) -> Dict[str, str]:
    headers = (message.get("payload") or {}).get("headers") or []
    return {h["name"]: h["value"] for h in headers if "name" in h and "value" in h}


def extract_body(message: Dict[str, Any]) -> str:
    """Prefer text/plain; fall back to a stripped text/html; walks multipart
    parts recursively (Gmail messages are frequently multipart/alternative)."""

    def _decode(data: str) -> str:
        try:
            return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _walk(part: Dict[str, Any]) -> Dict[str, str]:
        found: Dict[str, str] = {}
        mime_type = part.get("mimeType", "")
        body_data = (part.get("body") or {}).get("data")
        if body_data and mime_type in ("text/plain", "text/html"):
            found.setdefault(mime_type, _decode(body_data))
        for sub_part in part.get("parts") or []:
            for k, v in _walk(sub_part).items():
                found.setdefault(k, v)
        return found

    payload = message.get("payload") or {}
    parts = _walk(payload)
    if "text/plain" in parts:
        return parts["text/plain"]
    if "text/html" in parts:
        import re
        return re.sub(r"<[^>]+>", "", parts["text/html"])
    return ""


def extract_references(headers: Dict[str, str]) -> List[str]:
    raw = headers.get("References", "")
    return [r.strip() for r in raw.split() if r.strip()]
