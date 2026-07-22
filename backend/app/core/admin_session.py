"""DB-backed opaque admin session tokens — replaces app/core/session_auth.py.

Token = secrets.token_urlsafe(32) (~256 bits of entropy from the CSPRNG).
Only sha256(token) is ever persisted (app/models/admin_session.py); the raw
token exists only in the HttpOnly cookie on the client and in the response
path here. Lookup is by the hash (indexed, unique) — equivalent
unguessability to an HMAC-signed token without needing a signing secret.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models.admin_session import AdminSession
from app.models.admin_user import AdminUser


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_session(
    db: AsyncSession,
    admin_user: AdminUser,
    *,
    remember_me: bool = False,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[str, AdminSession]:
    """Issues a new session, returns (raw_token, AdminSession row).
    Caller is responsible for committing."""
    settings = get_settings()
    ttl = (
        timedelta(days=settings.ADMIN_SESSION_REMEMBER_TTL_DAYS)
        if remember_me
        else timedelta(hours=settings.ADMIN_SESSION_TTL_HOURS)
    )
    raw_token = secrets.token_urlsafe(32)
    session = AdminSession(
        admin_user_id=admin_user.id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.utcnow() + ttl,
        remember_me=remember_me,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:512] or None,
    )
    db.add(session)
    await db.flush()
    return raw_token, session


async def verify_session(db: AsyncSession, raw_token: Optional[str]) -> Optional[AdminUser]:
    """Returns the active AdminUser for a well-formed, unexpired,
    non-revoked session token, else None. Also touches last_seen_at
    (best-effort, not awaited-critical)."""
    if not raw_token:
        return None

    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(AdminSession, AdminUser)
        .join(AdminUser, AdminUser.id == AdminSession.admin_user_id)
        .where(AdminSession.token_hash == token_hash)
    )
    row = result.first()
    if row is None:
        return None
    session, admin_user = row

    if session.revoked_at is not None:
        return None
    if session.expires_at < datetime.utcnow():
        return None
    if not admin_user.is_active:
        return None

    await db.execute(
        update(AdminSession)
        .where(AdminSession.id == session.id)
        .values(last_seen_at=datetime.utcnow())
    )
    return admin_user


async def revoke_session_by_token(db: AsyncSession, raw_token: str) -> None:
    await db.execute(
        update(AdminSession)
        .where(AdminSession.token_hash == _hash_token(raw_token))
        .values(revoked_at=datetime.utcnow())
    )


async def revoke_session_by_id(db: AsyncSession, admin_user_id: UUID, session_id: UUID) -> bool:
    """Revokes a session by id, scoped to the owning admin (so one admin
    can't revoke another's session). Returns True if a row was affected."""
    result = await db.execute(
        update(AdminSession)
        .where(
            AdminSession.id == session_id,
            AdminSession.admin_user_id == admin_user_id,
            AdminSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.utcnow())
    )
    return result.rowcount > 0


async def revoke_all_sessions(db: AsyncSession, admin_user_id: UUID, *, except_token: Optional[str] = None) -> None:
    exclude_hash = _hash_token(except_token) if except_token else None
    stmt = update(AdminSession).where(
        AdminSession.admin_user_id == admin_user_id,
        AdminSession.revoked_at.is_(None),
    )
    if exclude_hash:
        stmt = stmt.where(AdminSession.token_hash != exclude_hash)
    await db.execute(stmt.values(revoked_at=datetime.utcnow()))
