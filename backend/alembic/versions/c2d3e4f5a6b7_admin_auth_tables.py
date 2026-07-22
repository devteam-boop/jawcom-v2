"""Admin auth tables — replaces the shared-workspace passcode

New tables only, purely additive:
  - admin_users: real per-admin accounts (Argon2id password_hash,
    role, lockout counters). Distinct from the dormant/unmigrated
    app/models/user.py 'users' table, which this migration does not touch.
  - admin_sessions: DB-backed opaque session tokens (only a SHA-256 hash
    is stored) — needed for "active sessions" / "terminate session".
  - password_reset_otps: forgot-password OTPs, hashed at rest.
  - admin_login_audit: login history / brute-force lockout / rate-limit
    lookback.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Each enum is used in exactly one column in this migration, so it's
# defined once and created implicitly by that column's create_table call
# (no separate explicit CREATE TYPE — doing both raced into
# DuplicateObjectError since the generic sa.Enum's create_type=False isn't
# honored by every SQLAlchemy DDL-visitor path here).
admin_role_enum = sa.Enum('admin', 'manager', 'agent', 'readonly', name='admin_role')
admin_audit_event_type_enum = sa.Enum(
    'login_success', 'login_failure', 'account_locked', 'logout', 'session_revoked',
    'password_reset_requested', 'password_reset_completed', 'password_changed',
    name='admin_audit_event_type',
)


def upgrade() -> None:
    op.create_table(
        'admin_users',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('role', admin_role_enum, nullable=False, server_default='admin'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_admin_users_email'),
    )
    op.create_index('ix_admin_users_email', 'admin_users', ['email'])

    op.create_table(
        'admin_sessions',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('admin_user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('remember_me', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(['admin_user_id'], ['admin_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_admin_sessions_token_hash'),
    )
    op.create_index('ix_admin_sessions_admin_user_id', 'admin_sessions', ['admin_user_id'])
    op.create_index('ix_admin_sessions_token_hash', 'admin_sessions', ['token_hash'])
    op.create_index('ix_admin_sessions_expires_at', 'admin_sessions', ['expires_at'])

    op.create_table(
        'password_reset_otps',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('admin_user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('otp_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('request_ip', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['admin_user_id'], ['admin_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_password_reset_otps_admin_user_id', 'password_reset_otps', ['admin_user_id'])
    op.create_index('ix_password_reset_otps_expires_at', 'password_reset_otps', ['expires_at'])

    op.create_table(
        'admin_login_audit',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('admin_user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('email_attempted', sa.String(length=255), nullable=False),
        sa.Column('event_type', admin_audit_event_type_enum, nullable=False),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['admin_user_id'], ['admin_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_admin_login_audit_admin_user_id', 'admin_login_audit', ['admin_user_id'])
    op.create_index('ix_admin_login_audit_email_attempted', 'admin_login_audit', ['email_attempted'])
    op.create_index('ix_admin_login_audit_event_type', 'admin_login_audit', ['event_type'])
    op.create_index('ix_admin_login_audit_created_at', 'admin_login_audit', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_admin_login_audit_created_at', table_name='admin_login_audit')
    op.drop_index('ix_admin_login_audit_event_type', table_name='admin_login_audit')
    op.drop_index('ix_admin_login_audit_email_attempted', table_name='admin_login_audit')
    op.drop_index('ix_admin_login_audit_admin_user_id', table_name='admin_login_audit')
    op.drop_table('admin_login_audit')

    op.drop_index('ix_password_reset_otps_expires_at', table_name='password_reset_otps')
    op.drop_index('ix_password_reset_otps_admin_user_id', table_name='password_reset_otps')
    op.drop_table('password_reset_otps')

    op.drop_index('ix_admin_sessions_expires_at', table_name='admin_sessions')
    op.drop_index('ix_admin_sessions_token_hash', table_name='admin_sessions')
    op.drop_index('ix_admin_sessions_admin_user_id', table_name='admin_sessions')
    op.drop_table('admin_sessions')

    op.drop_index('ix_admin_users_email', table_name='admin_users')
    op.drop_table('admin_users')

    bind = op.get_bind()
    admin_audit_event_type_enum.drop(bind, checkfirst=True)
    admin_role_enum.drop(bind, checkfirst=True)
