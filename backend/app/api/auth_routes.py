"""Admin login/logout/session + forgot-password OTP flow.

Replaces the old shared-workspace-passcode /api/auth/login (see
app/core/jawis_auth_middleware.py for the full auth architecture). Real
per-admin accounts, Argon2id password hashes, DB-backed session cookies,
brute-force lockout, and an OTP-based reset flow where the code goes to a
FIXED internal mailbox (ADMIN_OTP_RECIPIENT_EMAIL) rather than the
requesting user — see app/services/admin_notification_service.py.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.admin_auth_dependency import get_current_admin
from app.core.admin_session import create_session, revoke_all_sessions, revoke_session_by_token
from app.core.csrf import CSRF_COOKIE_NAME, generate_csrf_token
from app.core.dependencies import get_db_session
from app.core.login_security import (
    client_ip,
    is_ip_rate_limited,
    is_locked,
    record_audit_event,
    register_failed_login,
    register_successful_login,
)
from app.core.otp import count_recent_otp_requests, create_otp, verify_and_consume_otp
from app.core.password_hashing import hash_password, validate_password_policy, verify_password
from app.models.admin_login_audit import AdminAuditEventType
from app.models.admin_user import AdminUser
from app.services.admin_notification_service import send_password_reset_otp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Auth"])

_GENERIC_RESET_RESPONSE = {
    "detail": "If that account exists, a reset code has been sent to the workspace administrator.",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    value = value.strip()
    if not _EMAIL_RE.match(value):
        raise ValueError("Invalid email address")
    return value


def _set_session_cookies(response: Response, *, raw_token: str, remember_me: bool) -> None:
    settings = get_settings()
    max_age = (
        settings.ADMIN_SESSION_REMEMBER_TTL_DAYS * 86400
        if remember_me
        else settings.ADMIN_SESSION_TTL_HOURS * 3600
    )
    cookie_kwargs = dict(
        secure=settings.ADMIN_SESSION_COOKIE_SECURE,
        samesite=settings.ADMIN_SESSION_COOKIE_SAMESITE,
        domain=settings.ADMIN_SESSION_COOKIE_DOMAIN,
        path="/",
        max_age=max_age,
    )
    response.set_cookie(settings.ADMIN_SESSION_COOKIE_NAME, raw_token, httponly=True, **cookie_kwargs)
    # Not HttpOnly — the frontend JS must be able to read this one to echo
    # it back as X-CSRF-Token (double-submit pattern, see app/core/csrf.py).
    response.set_cookie(CSRF_COOKIE_NAME, generate_csrf_token(), httponly=False, **cookie_kwargs)


def _clear_session_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.ADMIN_SESSION_COOKIE_NAME, path="/", domain=settings.ADMIN_SESSION_COOKIE_DOMAIN)
    response.delete_cookie(CSRF_COOKIE_NAME, path="/", domain=settings.ADMIN_SESSION_COOKIE_DOMAIN)


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False

    _validate_email = field_validator("email")(_validate_email)


class AdminUserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    last_login_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    user: AdminUserOut


@router.post("/login", response_model=LoginResponse, summary="Admin login")
async def login(request: LoginRequest, http_request: Request, response: Response, db: AsyncSession = Depends(get_db_session)):
    ip = client_ip(http_request)
    ua = http_request.headers.get("user-agent")
    email = request.email.lower().strip()

    if await is_ip_rate_limited(db, ip):
        await record_audit_event(db, event_type=AdminAuditEventType.LOGIN_FAILURE, email_attempted=email, ip_address=ip, user_agent=ua, detail="rate_limited")
        await db.commit()
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    result = await db.execute(select(AdminUser).where(AdminUser.email == email))
    admin_user = result.scalar_one_or_none()

    # Constant-shape failure path regardless of whether the account exists,
    # is inactive, is locked, or the password is simply wrong — never
    # reveal which case it was.
    if admin_user is None or not admin_user.is_active:
        await record_audit_event(db, event_type=AdminAuditEventType.LOGIN_FAILURE, email_attempted=email, ip_address=ip, user_agent=ua, detail="no_such_active_account")
        await db.commit()
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if is_locked(admin_user):
        await record_audit_event(db, event_type=AdminAuditEventType.LOGIN_FAILURE, email_attempted=email, admin_user_id=admin_user.id, ip_address=ip, user_agent=ua, detail="account_locked")
        await db.commit()
        raise HTTPException(status_code=401, detail="Account temporarily locked due to repeated failed attempts. Try again later.")

    if not verify_password(request.password, admin_user.password_hash):
        await register_failed_login(db, admin_user)
        locked_now = is_locked(admin_user)
        await record_audit_event(
            db,
            event_type=AdminAuditEventType.ACCOUNT_LOCKED if locked_now else AdminAuditEventType.LOGIN_FAILURE,
            email_attempted=email, admin_user_id=admin_user.id, ip_address=ip, user_agent=ua,
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    await register_successful_login(db, admin_user)
    await record_audit_event(db, event_type=AdminAuditEventType.LOGIN_SUCCESS, email_attempted=email, admin_user_id=admin_user.id, ip_address=ip, user_agent=ua)
    raw_token, _session = await create_session(db, admin_user, remember_me=request.remember_me, ip_address=ip, user_agent=ua)
    await db.commit()

    _set_session_cookies(response, raw_token=raw_token, remember_me=request.remember_me)
    return LoginResponse(user=AdminUserOut(
        id=str(admin_user.id), email=admin_user.email, full_name=admin_user.full_name,
        role=admin_user.role.value, last_login_at=admin_user.last_login_at,
    ))


@router.post("/logout", summary="Log out the current session")
async def logout(http_request: Request, response: Response, db: AsyncSession = Depends(get_db_session)):
    settings = get_settings()
    raw_token = http_request.cookies.get(settings.ADMIN_SESSION_COOKIE_NAME)
    if raw_token:
        admin_user = getattr(http_request.state, "admin_user", None)
        await revoke_session_by_token(db, raw_token)
        if admin_user is not None:
            await record_audit_event(
                db, event_type=AdminAuditEventType.LOGOUT, email_attempted=admin_user.email,
                admin_user_id=admin_user.id, ip_address=client_ip(http_request),
                user_agent=http_request.headers.get("user-agent"),
            )
        await db.commit()
    _clear_session_cookies(response)
    return {"detail": "Logged out"}


@router.get("/me", response_model=AdminUserOut, summary="Current logged-in admin")
async def me(admin_user: AdminUser = Depends(get_current_admin)):
    return AdminUserOut(
        id=str(admin_user.id), email=admin_user.email, full_name=admin_user.full_name,
        role=admin_user.role.value, last_login_at=admin_user.last_login_at,
    )


class ForgotPasswordRequest(BaseModel):
    email: str

    _validate_email = field_validator("email")(_validate_email)


@router.post(
    "/forgot-password",
    summary="Request a password reset — OTP is emailed to the workspace administrator, never to the requester",
)
async def forgot_password(request: ForgotPasswordRequest, http_request: Request, db: AsyncSession = Depends(get_db_session)):
    ip = client_ip(http_request)
    email = request.email.lower().strip()
    settings = get_settings()

    result = await db.execute(select(AdminUser).where(AdminUser.email == email))
    admin_user = result.scalar_one_or_none()

    # Always the same response whether or not the account exists — must
    # not let an attacker enumerate valid admin emails.
    if admin_user is None or not admin_user.is_active:
        await record_audit_event(db, event_type=AdminAuditEventType.PASSWORD_RESET_REQUESTED, email_attempted=email, ip_address=ip, detail="no_such_active_account")
        await db.commit()
        return _GENERIC_RESET_RESPONSE

    recent = await count_recent_otp_requests(db, admin_user.id, since_minutes=60)
    if recent >= settings.ADMIN_OTP_MAX_REQUESTS_PER_HOUR:
        await record_audit_event(db, event_type=AdminAuditEventType.PASSWORD_RESET_REQUESTED, email_attempted=email, admin_user_id=admin_user.id, ip_address=ip, detail="rate_limited")
        await db.commit()
        return _GENERIC_RESET_RESPONSE

    otp_code = await create_otp(db, admin_user.id, request_ip=ip)
    await record_audit_event(db, event_type=AdminAuditEventType.PASSWORD_RESET_REQUESTED, email_attempted=email, admin_user_id=admin_user.id, ip_address=ip)
    await db.commit()

    sent = await send_password_reset_otp(
        requester_name=admin_user.full_name, requester_email=admin_user.email, otp=otp_code, ip_address=ip,
    )
    if not sent:
        logger.error("Password-reset OTP could not be emailed for account %s", admin_user.email)

    return _GENERIC_RESET_RESPONSE


class ResetPasswordRequest(BaseModel):
    email: str
    otp: str = Field(min_length=6, max_length=6)
    new_password: str

    _validate_email = field_validator("email")(_validate_email)


@router.post("/reset-password", summary="Complete a password reset using the OTP relayed by the administrator")
async def reset_password(request: ResetPasswordRequest, http_request: Request, db: AsyncSession = Depends(get_db_session)):
    ip = client_ip(http_request)
    email = request.email.lower().strip()

    result = await db.execute(select(AdminUser).where(AdminUser.email == email))
    admin_user = result.scalar_one_or_none()
    if admin_user is None or not admin_user.is_active:
        # Same generic error the OTP-mismatch path returns — no account
        # enumeration here either.
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    if not await verify_and_consume_otp(db, admin_user.id, request.otp):
        await record_audit_event(db, event_type=AdminAuditEventType.LOGIN_FAILURE, email_attempted=email, admin_user_id=admin_user.id, ip_address=ip, detail="bad_reset_otp")
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    policy_error = validate_password_policy(request.new_password)
    if policy_error:
        raise HTTPException(status_code=400, detail=policy_error)

    admin_user.password_hash = hash_password(request.new_password)
    admin_user.password_changed_at = datetime.utcnow()
    admin_user.failed_login_attempts = 0
    admin_user.locked_until = None
    await revoke_all_sessions(db, admin_user.id)
    await record_audit_event(db, event_type=AdminAuditEventType.PASSWORD_RESET_COMPLETED, email_attempted=email, admin_user_id=admin_user.id, ip_address=ip)
    await db.commit()

    return {"detail": "Password has been reset. Please log in with your new password."}
