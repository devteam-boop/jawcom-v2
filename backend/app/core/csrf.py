"""Double-submit-cookie CSRF protection.

Needed because the session lives in a cookie sent automatically by the
browser — a malicious cross-origin page can trigger the request, but it
cannot read another origin's cookies, so it cannot learn the CSRF token to
put in the required header. Issued as its own non-HttpOnly cookie
(JS on the legitimate frontend origin reads it and echoes it back as a
header) alongside the HttpOnly session cookie on every successful login.
Verified in app/core/jawis_auth_middleware.py for every state-changing
(non-GET/HEAD/OPTIONS) request on an admin-session-protected route.
"""

import hmac
import secrets

CSRF_COOKIE_NAME = "jawcom_csrf"
CSRF_HEADER_NAME = "x-csrf-token"

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def requires_csrf_check(method: str) -> bool:
    return method.upper() not in _SAFE_METHODS


def csrf_token_valid(cookie_value: str, header_value: str) -> bool:
    if not cookie_value or not header_value:
        return False
    return hmac.compare_digest(cookie_value, header_value)
