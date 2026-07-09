"""Create email_sync_state; make the pmid+event_type uniqueness partial (exclude replied)

Two changes, bundled because the second depends on understanding why the
first exists:

1. email_sync_state — new table (Gmail reply-sync cursor persistence, see
   app/models/email_sync_state.py). Not a duplicate of communication_events
   — this tracks sync execution state, not a communication event.

2. uq_communication_events_pmid_event_type (added in c1d2e3f4a5b7) was a
   plain UNIQUE(provider_message_id, event_type). That's correct for
   delivered/opened/clicked/bounced/complained/email_sent/failed (each can
   only legitimately occur once per outbound message), but wrong for
   'replied': a single email thread can receive multiple genuine, separate
   replies, all correlating to the same provider_message_id anchor. Under
   the old plain constraint, a second real reply would be rejected by the
   DB and silently dropped as a false "duplicate". Replaced with a partial
   unique index that excludes event_type='replied' — reply-specific
   idempotency (retries/reprocessing of the *same* inbound Gmail message)
   is enforced at the application level instead, keyed on the Gmail
   message's own Message-ID.

Revision ID: d2e3f4a5b6c8
Revises: c1d2e3f4a5b7
Create Date: 2026-07-09 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c8'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'email_sync_state',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('sync_name', sa.String(length=100), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_email_sync_state_sync_name', 'email_sync_state', ['sync_name'], unique=True)

    op.drop_constraint(
        'uq_communication_events_pmid_event_type',
        'communication_events',
        type_='unique',
    )
    op.create_index(
        'uq_communication_events_pmid_event_type',
        'communication_events',
        ['provider_message_id', 'event_type'],
        unique=True,
        postgresql_where=sa.text("event_type != 'replied'"),
    )


def downgrade() -> None:
    op.drop_index('uq_communication_events_pmid_event_type', table_name='communication_events')
    op.create_unique_constraint(
        'uq_communication_events_pmid_event_type',
        'communication_events',
        ['provider_message_id', 'event_type'],
    )

    op.drop_index('ix_email_sync_state_sync_name', table_name='email_sync_state')
    op.drop_table('email_sync_state')
