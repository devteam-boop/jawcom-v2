"""Create communication_events table

New table only — no changes to any existing table. Canonical, append-only
log of communication-domain events (journey start, node execution, message
send, task lifecycle). Distinct from flow_execution_logs (internal
node-execution debug trail, unchanged by this migration).

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-07-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'communication_events',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('running_instance_id', UUID(as_uuid=True), nullable=False),
        sa.Column('journey_id', UUID(as_uuid=True), nullable=True),
        sa.Column('lead_id', sa.BigInteger(), nullable=False),
        sa.Column('node_id', sa.String(length=255), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False, server_default='system'),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('payload', JSON(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['running_instance_id'], ['running_journey_instances.id']),
        sa.ForeignKeyConstraint(['journey_id'], ['journeys.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.alter_column('communication_events', 'channel', server_default=None)

    op.create_index('ix_communication_events_running_instance_id',
                     'communication_events', ['running_instance_id'])
    op.create_index('ix_communication_events_journey_id',
                     'communication_events', ['journey_id'])
    op.create_index('ix_communication_events_lead_id',
                     'communication_events', ['lead_id'])
    op.create_index('ix_communication_events_event_type',
                     'communication_events', ['event_type'])
    op.create_index('ix_communication_events_provider_message_id',
                     'communication_events', ['provider_message_id'])


def downgrade() -> None:
    op.drop_index('ix_communication_events_provider_message_id', table_name='communication_events')
    op.drop_index('ix_communication_events_event_type', table_name='communication_events')
    op.drop_index('ix_communication_events_lead_id', table_name='communication_events')
    op.drop_index('ix_communication_events_journey_id', table_name='communication_events')
    op.drop_index('ix_communication_events_running_instance_id', table_name='communication_events')
    op.drop_table('communication_events')
