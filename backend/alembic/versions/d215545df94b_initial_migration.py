"""Initial migration

Revision ID: d215545df94b
Revises: 
Create Date: 2026-07-03 11:44:34.237560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd215545df94b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Tables with no FK dependencies ---
    op.create_table('workspaces',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    # --- flow_definitions <-> journeys circular dependency ---
    # Create both tables without the circular FKs, then add them via ALTER TABLE.
    op.create_table('flow_definitions',
        sa.Column('definition', sa.Text(), nullable=False),
        sa.Column('journey_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('journeys',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'PAUSED', 'ARCHIVED', name='journeystatus'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('flow_definition_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    # Add the circular FKs now that both tables exist.
    op.create_foreign_key(
        'fk_flow_definitions_journey', 'flow_definitions', 'journeys',
        ['journey_id'], ['id'],
    )
    op.create_foreign_key(
        'fk_journeys_flow_definition', 'journeys', 'flow_definitions',
        ['flow_definition_id'], ['id'],
    )

    # --- Tables referencing workspaces ---
    op.create_table('users',
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'MEMBER', 'VIEWER', name='userrole'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_table('templates',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('channel', sa.Enum('EMAIL', 'SMS', 'WHATSAPP', 'PUSH', name='templatechannel'), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'INACTIVE', name='templatestatus'), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('conversations',
        sa.Column('channel', sa.Enum('EMAIL', 'SMS', 'WHATSAPP', 'PUSH', name='conversationchannel'), nullable=False),
        sa.Column('recipient_id', sa.String(length=255), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- Tables referencing workspaces + templates ---
    op.create_table('campaigns',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'SCHEDULED', 'RUNNING', 'COMPLETED', 'CANCELLED', name='campaignstatus'), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('messages',
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('direction', sa.Enum('INBOUND', 'OUTBOUND', name='messagedirection'), nullable=False),
        sa.Column('status', sa.Enum('SENT', 'DELIVERED', 'READ', 'FAILED', name='messagestatus'), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('template_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- Tables referencing journeys (which now exist with all FKs) ---
    op.create_table('running_journey_instances',
        sa.Column('status', sa.Enum('RUNNING', 'COMPLETED', 'FAILED', 'WAITING', name='instancestatus'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('current_stage_id', sa.UUID(), nullable=True),
        sa.Column('journey_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['journey_id'], ['journeys.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('stage_mappings',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('journey_id', sa.UUID(), nullable=False),
        sa.Column('template_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['journey_id'], ['journeys.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('campaign_recipients',
        sa.Column('recipient_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'DELIVERED', 'FAILED', name='recipientstatus'), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('campaign_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('campaign_recipients')
    op.drop_table('stage_mappings')
    op.drop_table('running_journey_instances')
    op.drop_table('messages')
    op.drop_table('campaigns')
    op.drop_table('conversations')
    op.drop_table('templates')
    op.drop_table('users')
    # Drop circular FKs before the involved tables.
    op.drop_constraint('fk_journeys_flow_definition', 'journeys', type_='foreignkey')
    op.drop_constraint('fk_flow_definitions_journey', 'flow_definitions', type_='foreignkey')
    op.drop_table('journeys')
    op.drop_table('flow_definitions')
    op.drop_table('workspaces')
