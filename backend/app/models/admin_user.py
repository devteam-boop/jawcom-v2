"""Real admin accounts — replaces the old shared-workspace passcode.

Single-tenant (no workspace_id — JawCom is one internal enterprise
instance, unlike the dormant app/models/user.py/workspace.py scaffolding
which was never migrated or wired up).

``role`` carries all four values the org wants (Admin/Manager/Agent/
ReadOnly) so a future role-scoped authorization layer is an additive
change (new checks against this column), not a schema migration. Today
every route that requires auth only checks "is there a valid session for
an active admin_users row" — role is not yet enforced anywhere.

``password_hash`` is nullable so a future SSO-only account (Google/
Microsoft/SAML/OIDC — see AUTH.md) can exist with no local password at
all, without a schema change. A future identity-provider link would be a
new additive table (admin_identity_providers: provider, provider_user_id,
admin_user_id FK) — not a redesign of this one.
"""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String

from .base import Base, BaseModel


class AdminRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    READONLY = "readonly"


class AdminUser(Base, BaseModel):
    __tablename__ = "admin_users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)
    role = Column(
        Enum(AdminRole, name="admin_role", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=AdminRole.ADMIN, nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
