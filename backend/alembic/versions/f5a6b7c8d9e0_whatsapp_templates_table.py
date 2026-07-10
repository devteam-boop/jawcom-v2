"""Create whatsapp_templates table (WhatsApp Template Management Phase 1)

New table, mirrors Meta's WhatsApp Business template catalog — see
app/models/whatsapp_template.py for why this is separate from the existing
generic `templates` table. Rows are only ever written by
WhatsAppTemplateService.sync_from_meta(); no seed/dummy data is inserted by
this migration (Feature 8 — "No dummy templates").

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'f5a6b7c8d9e0'
down_revision: Union[str, Sequence[str], None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'whatsapp_templates',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('provider_template_id', sa.String(length=255), nullable=False),
        sa.Column('template_name', sa.String(length=255), nullable=False),
        sa.Column('language', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('header_type', sa.String(length=20), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('footer', sa.Text(), nullable=True),
        sa.Column('buttons', sa.JSON(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_whatsapp_templates_provider_template_id',
        'whatsapp_templates', ['provider_template_id'], unique=True,
    )
    op.create_index(
        'ix_whatsapp_templates_template_name',
        'whatsapp_templates', ['template_name'],
    )
    op.create_index(
        'ix_whatsapp_templates_status',
        'whatsapp_templates', ['status'],
    )
    op.create_index(
        'uq_whatsapp_templates_name_language',
        'whatsapp_templates', ['template_name', 'language'], unique=True,
    )


def downgrade() -> None:
    op.drop_index('uq_whatsapp_templates_name_language', table_name='whatsapp_templates')
    op.drop_index('ix_whatsapp_templates_status', table_name='whatsapp_templates')
    op.drop_index('ix_whatsapp_templates_template_name', table_name='whatsapp_templates')
    op.drop_index('ix_whatsapp_templates_provider_template_id', table_name='whatsapp_templates')
    op.drop_table('whatsapp_templates')
