"""Auth gate for every route in the app — ASGI middleware (not per-route
Depends()) so the check runs before FastAPI resolves the route, parses the
body, or executes any business logic, for every HTTP method.

Three distinct credential types, deliberately not interchangeable:

  - /api/leads/{lead_id}/journey/* — JAWIS-only (machine-to-machine).
    Accepts only the shared JAWCOM_API_TOKEN bearer token. An admin's
    browser session is NEVER accepted here, so a leaked admin session can
    never be used to impersonate JAWIS.

  - /api/messages/* (send_email, send_whatsapp, ...) — accepts EITHER the
    JAWCOM_API_TOKEN (JAWIS's own manual-send/template-picker calls) OR a
    valid admin session cookie (the Inbox composer's manual Send). This is
    the only overlap between the two credential types, by design.

  - Everything else under /api/* — admin session cookie REQUIRED. This is
    the "Only authenticated Admin users may access JawCom" requirement:
    Dashboard, Contacts, Journeys, Templates, Campaigns,
    /api/communication-events, etc. were previously open with no auth at
    all; they now all require a logged-in admin, with NO secondary
    passcode prompt anywhere after login.

A handful of routes stay genuinely public because they're called by
something other than an authenticated admin's browser: /health (platform
health checks), /api/auth/login + forgot/reset-password (pre-auth by
definition), /api/webhooks/meta + /api/webhooks/resend (signature-verified
inbound provider webhooks), /api/webhooks/jawis (inbound JAWIS event
bridge — unchanged, out of scope for this task), /api/email-sync/run (its
own X-Webhook-Token, see app/api/email_sync_routes.py), and the OpenAPI/
docs endpoints.

CSRF: any state-changing request (non-GET/HEAD/OPTIONS) authenticated via
the admin session cookie must also carry a matching X-CSRF-Token header
(double-submit cookie — see app/core/csrf.py). JAWIS's bearer-token calls
are exempt (server-to-server, no ambient browser credential, nothing for
CSRF to exploit).
"""

import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config.settings import get_settings
from app.core.admin_session import verify_session
from app.core.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, csrf_token_valid, requires_csrf_check
from app.database.session import async_session_maker

_JAWIS_ONLY_PATTERNS = (
    re.compile(r"^/api/leads/[^/]+/journey(/|$)"),
)
_AGENT_OR_JAWIS_PATTERNS = (
    re.compile(r"^/api/messages(/|$)"),
)
_PUBLIC_EXACT = {
    "/health",
    "/api/auth/login",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/webhooks/jawis",
    "/api/openapi.json",
    "/docs",
    "/redoc",
}
_PUBLIC_PREFIXES = (
    "/api/webhooks/meta",
    "/api/webhooks/resend",
    "/api/email-sync",
)


def _matches_any(path: str, patterns) -> bool:
    return any(p.match(path) for p in patterns)


def _is_public(path: str) -> bool:
    if path in _PUBLIC_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in _PUBLIC_PREFIXES)


class JawisAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if not path.startswith("/api/") and path not in _PUBLIC_EXACT:
            # Nothing is served outside /api/* today (see app/main.py) —
            # leave anything else untouched rather than guessing.
            return await call_next(request)

        if _is_public(path):
            return await call_next(request)

        jawis_only = _matches_any(path, _JAWIS_ONLY_PATTERNS)
        agent_or_jawis = _matches_any(path, _AGENT_OR_JAWIS_PATTERNS)

        settings = get_settings()
        auth_header = request.headers.get("authorization", "")
        bearer_token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
        is_jawis = bool(settings.JAWCOM_API_TOKEN and bearer_token and bearer_token == settings.JAWCOM_API_TOKEN)

        if jawis_only:
            if not is_jawis:
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
            return await call_next(request)

        if is_jawis and agent_or_jawis:
            return await call_next(request)

        # Every remaining path (including /api/messages/* when the caller
        # isn't JAWIS) requires a logged-in admin.
        session_cookie = request.cookies.get(settings.ADMIN_SESSION_COOKIE_NAME)
        async with async_session_maker() as db:
            admin_user = await verify_session(db, session_cookie)
            await db.commit()

        if admin_user is None:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        if requires_csrf_check(request.method):
            csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME, "")
            csrf_header = request.headers.get(CSRF_HEADER_NAME, "")
            if not csrf_token_valid(csrf_cookie, csrf_header):
                return JSONResponse({"detail": "CSRF token missing or invalid"}, status_code=403)

        request.state.admin_user = admin_user
        return await call_next(request)
