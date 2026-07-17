"""Agent login for the JawCom frontend — see app/core/session_auth.py for
the full rationale (shared-workspace passcode, not multi-user auth).
"""

import hmac

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config.settings import get_settings
from app.core.session_auth import create_session_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in_seconds: int = 12 * 60 * 60


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in as a JawCom agent (shared workspace passcode)",
    description="Exchanges JAWCOM_APP_PASSWORD for a session token scoped to "
                "/api/messages/* only. Returns 503 if JAWCOM_APP_PASSWORD/"
                "JAWCOM_SESSION_SECRET aren't configured, 401 on a wrong password.",
)
async def login(request: LoginRequest):
    settings = get_settings()
    if not settings.JAWCOM_APP_PASSWORD or not settings.JAWCOM_SESSION_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Agent login not configured — set JAWCOM_APP_PASSWORD and JAWCOM_SESSION_SECRET",
        )
    if not hmac.compare_digest(request.password, settings.JAWCOM_APP_PASSWORD):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_session_token()
    if not token:
        raise HTTPException(status_code=503, detail="Agent login not configured")
    return LoginResponse(token=token)
