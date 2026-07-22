"""FastAPI dependency for routes that need the logged-in AdminUser object.

app/core/jawis_auth_middleware.py already rejects the request with 401
before any route handler runs if there's no valid admin session on a
protected path — this dependency just reads the AdminUser the middleware
already attached to request.state, so route code doesn't re-verify auth.
"""

from fastapi import HTTPException, Request

from app.models.admin_user import AdminUser


def get_current_admin(request: Request) -> AdminUser:
    admin_user = getattr(request.state, "admin_user", None)
    if admin_user is None:
        # Should be unreachable on a middleware-protected path — fails
        # closed if this dependency is ever used on an unprotected one.
        raise HTTPException(status_code=401, detail="Unauthorized")
    return admin_user
