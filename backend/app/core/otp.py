"""Forgot-password OTP generation/verification.

6-digit numeric code, generated with the CSPRNG (not `random`). Only the
SHA-256 hash is persisted (app/models/password_reset_otp.py); single-use
(``used_at``) and time-limited (ADMIN_OTP_TTL_MINUTES). The plaintext code
is returned once, to the caller, purely so it can be emailed — it is never
logged and never stored.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models.password_reset_otp import PasswordResetOTP


def _hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def create_otp(db: AsyncSession, admin_user_id: UUID, *, request_ip: Optional[str] = None) -> str:
    settings = get_settings()
    code = generate_otp_code()
    otp = PasswordResetOTP(
        admin_user_id=admin_user_id,
        otp_hash=_hash_otp(code),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.ADMIN_OTP_TTL_MINUTES),
        request_ip=request_ip,
    )
    db.add(otp)
    await db.flush()
    return code


async def verify_and_consume_otp(db: AsyncSession, admin_user_id: UUID, code: str) -> bool:
    """True and marks used_at iff a matching, unused, unexpired OTP exists
    for this account. Always checks against the most recent OTP row(s) so
    an old, superseded code can't be replayed."""
    otp_hash = _hash_otp(code)
    result = await db.execute(
        select(PasswordResetOTP).where(
            PasswordResetOTP.admin_user_id == admin_user_id,
            PasswordResetOTP.otp_hash == otp_hash,
            PasswordResetOTP.used_at.is_(None),
            PasswordResetOTP.expires_at >= datetime.utcnow(),
        )
    )
    otp = result.scalar_one_or_none()
    if otp is None:
        return False
    otp.used_at = datetime.utcnow()
    await db.flush()
    return True


async def count_recent_otp_requests(db: AsyncSession, admin_user_id: UUID, *, since_minutes: int) -> int:
    result = await db.execute(
        select(PasswordResetOTP).where(
            PasswordResetOTP.admin_user_id == admin_user_id,
            PasswordResetOTP.created_at >= datetime.utcnow() - timedelta(minutes=since_minutes),
        )
    )
    return len(result.all())
