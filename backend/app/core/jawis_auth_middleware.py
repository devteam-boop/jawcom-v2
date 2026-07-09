"""Bearer-token authentication for JAWIS-facing routes.

Implemented as ASGI middleware (not a per-route Depends()) so the check is
guaranteed to run before FastAPI resolves the route, parses the request
body, or executes any business logic — including request validation (e.g.
the required `stage` field) — for every HTTP method, not just POST.

Protects exactly the three route patterns named in the spec:
  - /api/messages/*
  - /api/communication-events (and /{event_id})
  - /api/leads/{lead_id}/journey/*
No other route is affected. /api/leads/{lead_id}/timeline is intentionally
NOT covered — it's outside the three listed patterns; flagged separately
rather than silently secured or left open.
"""

import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config.settings import get_settings

_PROTECTED_PATTERNS = (
    re.compile(r"^/api/messages(/|$)"),
    re.compile(r"^/api/communication-events(/|$)"),
    re.compile(r"^/api/leads/[^/]+/journey(/|$)"),
)


def _is_protected(path: str) -> bool:
    return any(p.match(path) for p in _PROTECTED_PATTERNS)


class JawisAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if _is_protected(request.url.path):
            settings = get_settings()
            expected = settings.JAWCOM_API_TOKEN
            auth_header = request.headers.get("authorization", "")
            token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
            if not expected or not token or token != expected:
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)
