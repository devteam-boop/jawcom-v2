"""Index audit follow-up: add reserved_at index on email_send_idempotency

The existing unique index (uq_email_send_idempotency_dedup_key, migration
c8d9e0f1a2b3) covers check_and_reserve()'s and record_provider_message_id()'s
by-dedup_key lookups, but scripts/cleanup_email_idempotency.py's DELETE
filters by reserved_at, not dedup_key — without this index that query would
plan a sequential scan once the table grows past a trivial size. Additive
only; does not touch the existing unique constraint or any other table.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-07-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd9e0f1a2b3c4'
down_revision: Union[str, Sequence[str], None] = 'c8d9e0f1a2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_email_send_idempotency_reserved_at',
        'email_send_idempotency',
        ['reserved_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_email_send_idempotency_reserved_at', table_name='email_send_idempotency')
