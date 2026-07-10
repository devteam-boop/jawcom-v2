"""Add jawis_synced_at to communication_events

A failed JAWIS webhook publish (see _publish_to_jawis,
communication_event_service.py) previously left no durable trace — only a
transient ERROR log line ("exhausted all retries"). There was no way to
query which rows JAWIS actually has a copy of vs. which never made it.

jawis_synced_at is set to the publish timestamp on a 2xx response and left
NULL otherwise (never attempted, mid-retry, or exhausted). NULL is the
queryable "needs resync" set the backfill script (scripts/backfill_jawis_sync.py)
targets. Existing rows are backfilled as NULL by definition, since no
tracking existed before this migration.

Revision ID: e4f5a6b7c8d9
Revises: d2e3f4a5b6c8
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, Sequence[str], None] = 'd2e3f4a5b6c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'communication_events',
        sa.Column('jawis_synced_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('communication_events', 'jawis_synced_at')
