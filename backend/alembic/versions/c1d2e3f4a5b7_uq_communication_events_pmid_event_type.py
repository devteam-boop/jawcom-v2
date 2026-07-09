"""Add unique constraint on communication_events(provider_message_id, event_type)

Guarantees webhook retries can never create duplicate rows at the database
level (the application-level exists_by_provider_message_id_and_type() check
in CommunicationEventService.record_inbound_status() has a check-then-insert
race under concurrent delivery; this constraint closes it). Rows with a NULL
provider_message_id (outbound send-failure events, internal Journey events)
are unaffected — SQL NULLs are never considered equal to each other in a
unique constraint.

Verified before writing this migration: zero existing (provider_message_id,
event_type) duplicates in the live table, so this is safe to apply directly.

Revision ID: c1d2e3f4a5b7
Revises: b4c5d6e7f8a9
Create Date: 2026-07-09 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b7'
down_revision: Union[str, Sequence[str], None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_communication_events_pmid_event_type',
        'communication_events',
        ['provider_message_id', 'event_type'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_communication_events_pmid_event_type',
        'communication_events',
        type_='unique',
    )
