"""Login/session audit trail — login history, brute-force/rate-limit
lookback, and the "Active sessions" / security views in Settings."""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, BaseModel


class AdminAuditEventType(str, enum.Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    ACCOUNT_LOCKED = "account_locked"
    LOGOUT = "logout"
    SESSION_REVOKED = "session_revoked"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    PASSWORD_CHANGED = "password_changed"


class AdminLoginAudit(Base, BaseModel):
    __tablename__ = "admin_login_audit"

    # Nullable: a LOGIN_FAILURE against an email with no matching account
    # still gets an audit row (for rate limiting / brute-force visibility),
    # but has no admin_user_id to point at.
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, index=True)
    email_attempted = Column(String(255), nullable=False, index=True)
    event_type = Column(
        Enum(AdminAuditEventType, name="admin_audit_event_type", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False, index=True,
    )
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    detail = Column(Text, nullable=True)
