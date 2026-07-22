"""Admin self-service: profile, change password, active sessions, login
history. All routes require an already-valid admin session — enforced by
app/core/jawis_auth_middleware.py before any handler here runs; the
Depends(get_current_admin) below just reads the AdminUser it attached.
"""

import hashlib
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.admin_auth_dependency import get_current_admin
from app.core.admin_session import revoke_all_sessions, revoke_session_by_id
from app.core.dependencies import get_db_session
from app.core.login_security import client_ip, record_audit_event
from app.core.password_hashing import hash_password, validate_password_policy, verify_password
from app.models.admin_login_audit import AdminAuditEventType, AdminLoginAudit
from app.models.admin_session import AdminSession
from app.models.admin_user import AdminUser

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)


class ProfileOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str


@router.patch("/profile", response_model=ProfileOut, summary="Update the current admin's display name")
async def update_profile(
    request: UpdateProfileRequest,
    admin_user: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    admin_user.full_name = request.full_name.strip()
    await db.commit()
    return ProfileOut(id=str(admin_user.id), email=admin_user.email, full_name=admin_user.full_name, role=admin_user.role.value)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password", summary="Change the current admin's password")
async def change_password(
    request: ChangePasswordRequest,
    http_request: Request,
    admin_user: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    if not verify_password(request.current_password, admin_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    policy_error = validate_password_policy(request.new_password)
    if policy_error:
        raise HTTPException(status_code=400, detail=policy_error)

    settings = get_settings()
    current_token = http_request.cookies.get(settings.ADMIN_SESSION_COOKIE_NAME)

    admin_user.password_hash = hash_password(request.new_password)
    admin_user.password_changed_at = datetime.utcnow()
    await revoke_all_sessions(db, admin_user.id, except_token=current_token)

    await record_audit_event(
        db, event_type=AdminAuditEventType.PASSWORD_CHANGED, email_attempted=admin_user.email,
        admin_user_id=admin_user.id, ip_address=client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )
    await db.commit()
    return {"detail": "Password changed. Other sessions have been signed out."}


class SessionOut(BaseModel):
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    expires_at: datetime
    remember_me: bool
    is_current: bool


@router.get("/sessions", response_model=List[SessionOut], summary="List this admin's active sessions")
async def list_sessions(
    http_request: Request,
    admin_user: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    settings = get_settings()
    current_token = http_request.cookies.get(settings.ADMIN_SESSION_COOKIE_NAME)
    current_hash = hashlib.sha256(current_token.encode("utf-8")).hexdigest() if current_token else None

    result = await db.execute(
        select(AdminSession)
        .where(
            AdminSession.admin_user_id == admin_user.id,
            AdminSession.revoked_at.is_(None),
            AdminSession.expires_at >= datetime.utcnow(),
        )
        .order_by(AdminSession.last_seen_at.desc().nullslast(), AdminSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [
        SessionOut(
            id=str(s.id), ip_address=s.ip_address, user_agent=s.user_agent,
            created_at=s.created_at, last_seen_at=s.last_seen_at, expires_at=s.expires_at,
            remember_me=s.remember_me, is_current=(s.token_hash == current_hash),
        )
        for s in sessions
    ]


@router.post("/sessions/{session_id}/revoke", summary="Terminate one of this admin's own sessions")
async def revoke_session(
    session_id: str,
    admin_user: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id")

    ok = await revoke_session_by_id(db, admin_user.id, session_uuid)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")

    await record_audit_event(
        db, event_type=AdminAuditEventType.SESSION_REVOKED, email_attempted=admin_user.email,
        admin_user_id=admin_user.id, detail=f"session_id={session_id}",
    )
    await db.commit()
    return {"detail": "Session revoked"}


class LoginHistoryEntry(BaseModel):
    event_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    detail: Optional[str] = None


@router.get("/login-history", response_model=List[LoginHistoryEntry], summary="Recent login/security events for this admin")
async def login_history(
    limit: int = 50,
    admin_user: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db_session),
):
    limit = max(1, min(limit, 200))
    result = await db.execute(
        select(AdminLoginAudit)
        .where(AdminLoginAudit.admin_user_id == admin_user.id)
        .order_by(AdminLoginAudit.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        LoginHistoryEntry(
            event_type=r.event_type.value, ip_address=r.ip_address, user_agent=r.user_agent,
            created_at=r.created_at, detail=r.detail,
        )
        for r in rows
    ]
