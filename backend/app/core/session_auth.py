"""Minimal agent session tokens for the JawCom frontend itself.

This is deliberately NOT a multi-user auth system (no user table, no
per-agent identity) — JawCom has none today and building one is out of
scope for a surgical fix. It is a single shared-workspace passcode
(JAWCOM_APP_PASSWORD): whoever has it can log in and get a signed,
short-lived, scope-limited token. That token is accepted only on
/api/messages/* (see jawis_auth_middleware.py) — never on the
JAWIS-facing journey-control routes — so a leaked agent session cannot be
used to impersonate JAWIS, and a leaked JAWIS token cannot be used here
either (different secret, different scope).

Stateless HMAC-signed token (no server-side session store, no new
dependency): payload is `<scope>.<exp>`, base64url-encoded, followed by an
HMAC-SHA256 signature keyed with JAWCOM_SESSION_SECRET. Verified with
hmac.compare_digest to avoid a timing side channel, same pattern already
used for Meta's webhook signature (app/api/meta_webhook_routes.py).
"""

import base64
import hashlib
import hmac
import time
from typing import Optional

from app.config.settings import get_settings

_SCOPE = "jawcom_agent"
_TOKEN_TTL_SECONDS = 12 * 60 * 60  # 12 hours


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session_token() -> Optional[str]:
    """Issue a new session token, or None if JAWCOM_SESSION_SECRET isn't configured."""
    settings = get_settings()
    if not settings.JAWCOM_SESSION_SECRET:
        return None
    exp = int(time.time()) + _TOKEN_TTL_SECONDS
    payload = f"{_SCOPE}.{exp}"
    payload_b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    signature = _sign(payload, settings.JAWCOM_SESSION_SECRET)
    return f"{payload_b64}.{signature}"


def verify_session_token(token: Optional[str]) -> bool:
    """True only for a well-formed, correctly-signed, unexpired token."""
    settings = get_settings()
    if not token or not settings.JAWCOM_SESSION_SECRET:
        return False
    try:
        payload_b64, signature = token.split(".", 1)
        payload = base64.urlsafe_b64decode(payload_b64.encode("ascii")).decode("utf-8")
        scope, exp_str = payload.split(".", 1)
    except (ValueError, UnicodeDecodeError):
        return False

    expected = _sign(payload, settings.JAWCOM_SESSION_SECRET)
    if not hmac.compare_digest(expected, signature):
        return False
    if scope != _SCOPE:
        return False
    try:
        exp = int(exp_str)
    except ValueError:
        return False
    return time.time() < exp
