"""Manual Email Send idempotency table

Adds email_send_idempotency (see app/models/email_send_idempotency.py) —
closes the "JAWIS retries POST /api/messages/email/send on timeout -> two
real Resend sends" gap. A new, isolated table; no existing table's schema
or data is touched. Manual Email only — no Journey Engine, WhatsApp, or
webhook-processing table is affected.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-07-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'email_send_idempotency',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dedup_key', sa.String(length=64), nullable=False),
        sa.Column('communication_event_id', UUID(as_uuid=True), nullable=False),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('reserved_at', sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint(
        'uq_email_send_idempotency_dedup_key',
        'email_send_idempotency',
        ['dedup_key'],
    )


def downgrade() -> None:
    op.drop_table('email_send_idempotency')
