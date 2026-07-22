"""Forgot-password OTPs.

The 6-digit code is emailed ONLY to settings.ADMIN_OTP_RECIPIENT_EMAIL
(sales@nextmovein.com) — never to the requesting account's own address —
see app/services/admin_notification_service.py and
app/api/auth_routes.py::forgot_password. Only ``otp_hash`` (SHA-256) is
persisted, single-use (``used_at``), short-lived (see
ADMIN_OTP_TTL_MINUTES), and rate-limited per account
(ADMIN_OTP_MAX_REQUESTS_PER_HOUR) — see app/core/otp.py.
"""

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, BaseModel


class PasswordResetOTP(Base, BaseModel):
    __tablename__ = "password_reset_otps"

    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False, index=True)
    otp_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    request_ip = Column(String(64), nullable=True)
