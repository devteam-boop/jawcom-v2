"""Migrate Journey Engine tables (journeys, stage_mappings, running_journey_instances)

Transforms the old-style tables from the initial migration with ALTER operations
to preserve existing data.

Revision ID: e7f8a9b0c1d2
Revises: d215545df94b
Create Date: 2026-07-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, Sequence[str], None] = 'd215545df94b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema – transform old tables with ALTER, preserving data."""

    # ------------------------------------------------------------------
    # journeys
    # ------------------------------------------------------------------
    # Drop FK constraints before dropping columns
    op.drop_constraint('fk_journeys_flow_definition', 'journeys', type_='foreignkey')
    op.drop_constraint('journeys_workspace_id_fkey', 'journeys', type_='foreignkey')

    # Drop old columns
    op.drop_column('journeys', 'workspace_id')
    op.drop_column('journeys', 'flow_definition_id')

    # Add new columns
    op.add_column('journeys',
        sa.Column('trigger_type', sa.String(length=50), nullable=False, server_default=''))
    op.add_column('journeys',
        sa.Column('trigger_value', sa.String(length=255), nullable=True))
    op.add_column('journeys',
        sa.Column('config', JSON(), nullable=False, server_default='{}'))

    # Remove server_default so future inserts must supply these
    op.alter_column('journeys', 'trigger_type', server_default=None)
    op.alter_column('journeys', 'config', server_default=None)

    # ------------------------------------------------------------------
    # stage_mappings
    # ------------------------------------------------------------------
    # Drop FK on template_id
    op.drop_constraint('stage_mappings_template_id_fkey', 'stage_mappings', type_='foreignkey')

    # Add new columns
    op.add_column('stage_mappings',
        sa.Column('stage_key', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('stage_mappings',
        sa.Column('channel', sa.String(length=50), nullable=True))
    op.add_column('stage_mappings',
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text('0')))
    op.add_column('stage_mappings',
        sa.Column('config', JSON(), nullable=False, server_default='{}'))

    op.alter_column('stage_mappings', 'stage_key', server_default=None)
    op.alter_column('stage_mappings', 'config', server_default=None)

    # --- Index for stage_mappings ---
    op.create_index('ix_stage_mappings_journey_id',
                    'stage_mappings', ['journey_id'])

    # ------------------------------------------------------------------
    # running_journey_instances
    # ------------------------------------------------------------------
    # Drop FK on conversation_id
    op.drop_constraint('running_journey_instances_conversation_id_fkey',
                       'running_journey_instances', type_='foreignkey')

    # Drop conversation_id column
    op.drop_column('running_journey_instances', 'conversation_id')

    # Rename current_stage_id -> current_stage_mapping_id
    op.alter_column('running_journey_instances', 'current_stage_id',
                    new_column_name='current_stage_mapping_id')

    # Add new columns
    op.add_column('running_journey_instances',
        sa.Column('lead_id', UUID(as_uuid=True), nullable=False,
                  server_default='00000000-0000-0000-0000-000000000000'))
    op.add_column('running_journey_instances',
        sa.Column('data', JSON(), nullable=False, server_default='{}'))

    # Add FK on current_stage_mapping_id
    op.create_foreign_key(
        'fk_running_journey_instances_stage_mapping',
        'running_journey_instances', 'stage_mappings',
        ['current_stage_mapping_id'], ['id'],
    )

    # Remove server_default from new columns
    op.alter_column('running_journey_instances', 'lead_id', server_default=None)
    op.alter_column('running_journey_instances', 'data', server_default=None)

    # --- Indexes for performance ---
    op.create_index('ix_running_journey_instances_lead_id',
                    'running_journey_instances', ['lead_id'])
    op.create_index('ix_running_journey_instances_journey_id',
                    'running_journey_instances', ['journey_id'])
    op.create_index('ix_running_journey_instances_status',
                    'running_journey_instances', ['status'])


def downgrade() -> None:
    """Downgrade – remove new columns and indexes, preserving existing data."""
    # Remove indexes
    op.drop_index('ix_stage_mappings_journey_id', table_name='stage_mappings')
    op.drop_index('ix_running_journey_instances_status',
                  table_name='running_journey_instances')
    op.drop_index('ix_running_journey_instances_journey_id',
                  table_name='running_journey_instances')
    op.drop_index('ix_running_journey_instances_lead_id',
                  table_name='running_journey_instances')

    # Revert running_journey_instances
    op.drop_constraint('fk_running_journey_instances_stage_mapping',
                       'running_journey_instances', type_='foreignkey')
    op.drop_column('running_journey_instances', 'data')
    op.drop_column('running_journey_instances', 'lead_id')
    op.alter_column('running_journey_instances', 'current_stage_mapping_id',
                    new_column_name='current_stage_id')
    op.add_column('running_journey_instances',
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=False,
                  server_default='00000000-0000-0000-0000-000000000000'))
    op.create_foreign_key(
        'running_journey_instances_conversation_id_fkey',
        'running_journey_instances', 'conversations',
        ['conversation_id'], ['id'],
    )
    op.alter_column('running_journey_instances', 'conversation_id', server_default=None)

    # Revert stage_mappings
    op.drop_column('stage_mappings', 'config')
    op.drop_column('stage_mappings', 'sort_order')
    op.drop_column('stage_mappings', 'channel')
    op.drop_column('stage_mappings', 'stage_key')
    op.create_foreign_key(
        'stage_mappings_template_id_fkey', 'stage_mappings', 'templates',
        ['template_id'], ['id'],
    )

    # Revert journeys
    op.drop_column('journeys', 'config')
    op.drop_column('journeys', 'trigger_value')
    op.drop_column('journeys', 'trigger_type')
    op.add_column('journeys',
        sa.Column('flow_definition_id', UUID(as_uuid=True), nullable=False,
                  server_default='00000000-0000-0000-0000-000000000000'))
    op.add_column('journeys',
        sa.Column('workspace_id', UUID(as_uuid=True), nullable=False,
                  server_default='00000000-0000-0000-0000-000000000000'))
    op.create_foreign_key(
        'fk_journeys_flow_definition', 'journeys', 'flow_definitions',
        ['flow_definition_id'], ['id'],
    )
    op.create_foreign_key(
        'journeys_workspace_id_fkey', 'journeys', 'workspaces',
        ['workspace_id'], ['id'],
    )
    op.alter_column('journeys', 'flow_definition_id', server_default=None)
    op.alter_column('journeys', 'workspace_id', server_default=None)
