"""Add per-row last_synced_at to whatsapp_templates

WhatsApp Template Management (Meta lifecycle, Step 0 gap): freshness was
only tracked at the sync-run level (email_sync_state, keyed by
sync_name="whatsapp_templates") — there was no per-row marker of when a
specific template was last confirmed against Meta. Needed by the
Approved/Submitted panel row spec (last_synced_at alongside status/
quality_rating/rejection_reason) and by the message_template_status_update
webhook handler, which updates a single row outside of a full sync pass.

Purely additive — nullable, no backfill required (existing rows simply
report unknown freshness until the next sync or webhook update touches
them).

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('whatsapp_templates', sa.Column('last_synced_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('whatsapp_templates', 'last_synced_at')
