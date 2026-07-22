"""Brute-force protection + audit logging for the admin login flow.

No Redis/new dependency: rate limiting and lockout are both backed by
existing tables (REDIS_URL is reserved for future workers, not configured
today). Per-account lockout uses a counter on admin_users
(failed_login_attempts/locked_until); per-IP rate limiting queries
admin_login_audit directly since it has no natural "reset" the way an
account counter does.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models.admin_login_audit import AdminAuditEventType, AdminLoginAudit
from app.models.admin_user import AdminUser


async def record_audit_event(
    db: AsyncSession,
    *,
    event_type: AdminAuditEventType,
    email_attempted: str,
    admin_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    detail: Optional[str] = None,
) -> None:
    db.add(
        AdminLoginAudit(
            admin_user_id=admin_user_id,
            email_attempted=email_attempted[:255],
            event_type=event_type,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:512] or None,
            detail=detail,
        )
    )
    await db.flush()


def is_locked(admin_user: AdminUser) -> bool:
    return bool(admin_user.locked_until and admin_user.locked_until > datetime.utcnow())


async def register_failed_login(db: AsyncSession, admin_user: AdminUser) -> None:
    settings = get_settings()
    admin_user.failed_login_attempts = (admin_user.failed_login_attempts or 0) + 1
    if admin_user.failed_login_attempts >= settings.ADMIN_LOGIN_MAX_ATTEMPTS:
        admin_user.locked_until = datetime.utcnow() + timedelta(minutes=settings.ADMIN_LOGIN_LOCKOUT_MINUTES)
    await db.flush()


async def register_successful_login(db: AsyncSession, admin_user: AdminUser) -> None:
    admin_user.failed_login_attempts = 0
    admin_user.locked_until = None
    admin_user.last_login_at = datetime.utcnow()
    await db.flush()


async def is_ip_rate_limited(db: AsyncSession, ip_address: Optional[str]) -> bool:
    if not ip_address:
        return False
    settings = get_settings()
    since = datetime.utcnow() - timedelta(minutes=settings.ADMIN_LOGIN_RATE_LIMIT_WINDOW_MINUTES)
    result = await db.execute(
        select(func.count(AdminLoginAudit.id)).where(
            AdminLoginAudit.ip_address == ip_address,
            AdminLoginAudit.event_type == AdminAuditEventType.LOGIN_FAILURE,
            AdminLoginAudit.created_at >= since,
        )
    )
    count = result.scalar_one()
    return count >= settings.ADMIN_LOGIN_RATE_LIMIT_PER_IP


def client_ip(request) -> Optional[str]:
    """Best-effort client IP: trusts X-Forwarded-For's first hop (Railway
    and most PaaS put the real client there) falling back to the direct
    peer address."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
