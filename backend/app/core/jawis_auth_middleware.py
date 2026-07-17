"""Bearer-token authentication for JAWIS-facing and agent-send routes.

Implemented as ASGI middleware (not a per-route Depends()) so the check is
guaranteed to run before FastAPI resolves the route, parses the request
body, or executes any business logic — including request validation (e.g.
the required `stage` field) — for every HTTP method, not just POST.

Two distinct route groups, two distinct secrets, deliberately not
interchangeable:
  - /api/leads/{lead_id}/journey/* — JAWIS-only. Accepts only the shared
    JAWCOM_API_TOKEN. A logged-in agent's session token is NEVER accepted
    here, so a leaked frontend session can never be used to start/resume a
    journey as if it were JAWIS.
  - /api/messages/* (send_email, send_whatsapp, ...) — accepts EITHER the
    JAWCOM_API_TOKEN (JAWIS) OR a valid agent session token (Phase 3, Task 1
    — see app/core/session_auth.py). This is what lets the Inbox composer's
    manual Send actually work without embedding the JAWIS shared secret in
    the frontend bundle: agents log in (POST /api/auth/login) with a
    separate, lower-privilege shared passcode and get a short-lived token
    scoped to sends only.

GET /api/communication-events (and /{event_id}) is intentionally NOT
protected: it's read-only (no POST exists on that router by design — see
app/api/communication_event_routes.py), JAWIS never calls it ("JAWIS pulls
nothing", per app/services/communication_event_service.py's _publish_to_jawis
docstring — JawCom pushes to JAWIS via webhook instead), and it's the
JawCom frontend's own primary data source (Inbox, Dashboard, Lead Activity,
Execution Drawer) — those call it directly from the browser with no bearer
token, same as the already-unprotected GET /api/leads/{lead_id}/timeline,
which returns the same underlying data scoped to one lead.
"""

import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config.settings import get_settings
from app.core.session_auth import verify_session_token

_JAWIS_ONLY_PATTERNS = (
    re.compile(r"^/api/leads/[^/]+/journey(/|$)"),
)
_AGENT_OR_JAWIS_PATTERNS = (
    re.compile(r"^/api/messages(/|$)"),
)


def _matches_any(path: str, patterns) -> bool:
    return any(p.match(path) for p in patterns)


class JawisAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        jawis_only = _matches_any(path, _JAWIS_ONLY_PATTERNS)
        agent_or_jawis = _matches_any(path, _AGENT_OR_JAWIS_PATTERNS)

        if jawis_only or agent_or_jawis:
            settings = get_settings()
            auth_header = request.headers.get("authorization", "")
            token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None

            is_jawis = bool(settings.JAWCOM_API_TOKEN and token and token == settings.JAWCOM_API_TOKEN)
            is_agent = agent_or_jawis and verify_session_token(token)

            if not (is_jawis or is_agent):
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)
