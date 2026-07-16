"""Journey-driven Send idempotency table

Adds journey_send_idempotency (see app/models/journey_send_idempotency.py) —
closes the "journey re-triggered by a webhook replay, or a node/journey
retry, re-sends an already-sent send_whatsapp/send_email step" gap. A new,
isolated table; no existing table's schema or data is touched. Journey
Engine sends only — the manual-send idempotency table
(email_send_idempotency) and its API are untouched.

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-07-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'journey_send_idempotency',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dedup_key', sa.String(length=64), nullable=False),
        sa.Column('lead_id', sa.BigInteger(), nullable=False),
        sa.Column('node_id', sa.String(length=255), nullable=True),
        sa.Column('reserved_at', sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint(
        'uq_journey_send_idempotency_dedup_key',
        'journey_send_idempotency',
        ['dedup_key'],
    )
    op.create_index(
        'ix_journey_send_idempotency_reserved_at',
        'journey_send_idempotency',
        ['reserved_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_journey_send_idempotency_reserved_at', table_name='journey_send_idempotency')
    op.drop_table('journey_send_idempotency')
