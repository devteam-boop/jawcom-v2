"""DB-backed opaque admin session tokens.

Deliberately not a stateless JWT: "active sessions" / "terminate session"
(required by this task) need a server-side row to list and revoke. The raw
token (secrets.token_urlsafe(32), ~256 bits) is handed to the browser as an
HttpOnly cookie and NEVER stored — only its SHA-256 hash lives here, so a
DB read (backup, replica lag exposure, etc.) can't be used to replay a
session. Verification is a hash lookup + hmac.compare_digest-safe equality
via the unique index, same non-guessability guarantee a signed token would
give, without needing a signing secret to protect.

``remember_me`` only affects the TTL used when the row is created
(app/core/admin_session.py) — no separate refresh-token table yet, but
nothing here precludes adding one later (a refresh token would just be
another column or sibling table keyed on admin_user_id).
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, BaseModel


class AdminSession(Base, BaseModel):
    __tablename__ = "admin_sessions"

    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    remember_me = Column(Boolean, default=False, nullable=False)
