"""Migrate Flow Definition Engine tables
(flow_definitions, flow_versions, flow_execution_logs)

Transforms the old-style flow_definitions table from the initial migration with
ALTER operations to preserve existing data. Creates flow_versions and
flow_execution_logs as new tables.

Revision ID: a2b3c4d5e6f7
Revises: e7f8a9b0c1d2
Create Date: 2026-07-03 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema – transform flow_definitions, create new tables."""

    # ------------------------------------------------------------------
    # Transform flow_definitions (preserve existing data)
    # ------------------------------------------------------------------
    # Create enum type before adding a column that uses it
    op.execute(
        "CREATE TYPE flowdefinitionstatus AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED')"
    )

    # Drop FK on journey_id (created in initial migration)
    op.drop_constraint('fk_flow_definitions_journey', 'flow_definitions', type_='foreignkey')

    # Drop old column
    op.drop_column('flow_definitions', 'journey_id')

    # Add new columns
    op.add_column('flow_definitions',
        sa.Column('name', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('flow_definitions',
        sa.Column('description', sa.Text(), nullable=True))
    op.add_column('flow_definitions',
        sa.Column('status',
                   sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED',
                           name='flowdefinitionstatus',
                           create_type=False),
                   nullable=False, server_default='DRAFT'))
    op.add_column('flow_definitions',
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')))

    # Change definition from Text to JSON
    op.execute(
        'ALTER TABLE flow_definitions ALTER COLUMN definition TYPE JSON USING definition::json'
    )

    # Remove server_defaults so future inserts must supply these
    op.alter_column('flow_definitions', 'name', server_default=None)
    op.alter_column('flow_definitions', 'status', server_default=None)
    op.alter_column('flow_definitions', 'version', server_default=None)

    # ------------------------------------------------------------------
    # flow_versions (new table)
    # ------------------------------------------------------------------
    op.create_table('flow_versions',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('flow_definition_id', UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('definition', JSON(), nullable=False),
        sa.Column('change_log', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['flow_definition_id'], ['flow_definitions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # ------------------------------------------------------------------
    # flow_execution_logs (new table)
    # ------------------------------------------------------------------
    op.create_table('flow_execution_logs',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('flow_definition_id', UUID(as_uuid=True), nullable=False),
        sa.Column('flow_version_id', UUID(as_uuid=True), nullable=True),
        sa.Column('running_instance_id', UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', UUID(as_uuid=True), nullable=False),
        sa.Column('node_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('input', JSON(), nullable=False),
        sa.Column('output', JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['flow_definition_id'], ['flow_definitions.id'], ),
        sa.ForeignKeyConstraint(['flow_version_id'], ['flow_versions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- Indexes for performance ---
    op.create_index('ix_flow_execution_logs_lead_id',
                    'flow_execution_logs', ['lead_id'])
    op.create_index('ix_flow_execution_logs_running_instance_id',
                    'flow_execution_logs', ['running_instance_id'])
    op.create_index('ix_flow_execution_logs_flow_definition_id',
                    'flow_execution_logs', ['flow_definition_id'])
    op.create_index('ix_flow_versions_flow_definition_id',
                    'flow_versions', ['flow_definition_id'])


def downgrade() -> None:
    """Downgrade – drop only new tables and revert flow_definitions changes."""
    # Drop new tables and their indexes
    op.drop_index('ix_flow_versions_flow_definition_id',
                  table_name='flow_versions')
    op.drop_index('ix_flow_execution_logs_flow_definition_id',
                  table_name='flow_execution_logs')
    op.drop_index('ix_flow_execution_logs_running_instance_id',
                  table_name='flow_execution_logs')
    op.drop_index('ix_flow_execution_logs_lead_id',
                  table_name='flow_execution_logs')
    op.drop_table('flow_execution_logs')
    op.drop_table('flow_versions')

    # Revert flow_definitions to original schema
    op.drop_column('flow_definitions', 'version')
    op.drop_column('flow_definitions', 'status')
    op.drop_column('flow_definitions', 'description')
    op.drop_column('flow_definitions', 'name')

    # Convert definition back from JSON to Text
    op.execute(
        'ALTER TABLE flow_definitions ALTER COLUMN definition TYPE TEXT USING definition::text'
    )

    # Restore old columns
    op.add_column('flow_definitions',
        sa.Column('journey_id', UUID(as_uuid=True), nullable=False,
                  server_default='00000000-0000-0000-0000-000000000000'))
    op.create_foreign_key(
        'fk_flow_definitions_journey', 'flow_definitions', 'journeys',
        ['journey_id'], ['id'],
    )
    op.alter_column('flow_definitions', 'journey_id', server_default=None)

    op.execute('DROP TYPE IF EXISTS flowdefinitionstatus')
