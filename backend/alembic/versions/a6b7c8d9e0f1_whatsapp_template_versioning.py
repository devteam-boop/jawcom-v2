"""WhatsApp Template Management Phase 2: versioning, quality/rejection tracking, usage counters

Conflict flagged and resolved per Step 0 audit: the original
uq_whatsapp_templates_name_language UNIQUE(template_name, language)
constraint (migration f5a6b7c8d9e0) is incompatible with Phase 5's version
history (multiple rows legitimately sharing the same name+language, one per
version) — it is dropped here, not merely extended. provider_template_id
stays the sync-time dedupe key (already unique on its own, now nullable to
allow local-only DRAFT rows that haven't been submitted to Meta yet).

family_id is backfilled with a fresh, independent UUID per existing row
(each pre-existing row becomes the sole version-1 member of its own new
family) — deliberately NOT the row's own id: TemplateService.get_template()
resolves a plain row id before ever falling back to treating the value as a
family_id, so if family_id ever equalled a row's own id, a Journey node
later configured with that family_id (to "follow latest approved" once a
second version exists) would always resolve to this one specific row
directly instead, silently defeating the whole mechanism.

Also adds last_error to email_sync_state (Phase 7 operational visibility
for "Sync Status") — additive/nullable, no effect on Gmail sync's existing
use of that table.

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-07-10 00:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'a6b7c8d9e0f1'
down_revision: Union[str, Sequence[str], None] = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('uq_whatsapp_templates_name_language', table_name='whatsapp_templates')

    op.alter_column('whatsapp_templates', 'provider_template_id', nullable=True)

    op.add_column('whatsapp_templates', sa.Column('header_text', sa.Text(), nullable=True))
    op.add_column('whatsapp_templates', sa.Column('header_media_url', sa.Text(), nullable=True))
    op.add_column('whatsapp_templates', sa.Column('examples', sa.JSON(), nullable=True))
    op.add_column('whatsapp_templates', sa.Column('family_id', UUID(as_uuid=True), nullable=True))
    op.add_column('whatsapp_templates', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('whatsapp_templates', sa.Column('quality_rating', sa.String(length=20), nullable=True))
    op.add_column('whatsapp_templates', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('whatsapp_templates', sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('whatsapp_templates', sa.Column('last_used_at', sa.DateTime(), nullable=True))

    # Per-row independent UUID (not a single blanket "= id" update — see
    # module docstring for why that would be wrong) via a Python loop:
    # simplest correct way to generate a distinct value per row without
    # depending on a specific Postgres version/extension for gen_random_uuid().
    connection = op.get_bind()
    whatsapp_templates = sa.table(
        'whatsapp_templates',
        sa.column('id', UUID(as_uuid=True)),
        sa.column('family_id', UUID(as_uuid=True)),
    )
    rows = connection.execute(
        sa.select(whatsapp_templates.c.id).where(whatsapp_templates.c.family_id.is_(None))
    ).fetchall()
    for (row_id,) in rows:
        connection.execute(
            whatsapp_templates.update()
            .where(whatsapp_templates.c.id == row_id)
            .values(family_id=uuid.uuid4())
        )
    op.alter_column('whatsapp_templates', 'family_id', nullable=False)

    op.create_index('ix_whatsapp_templates_family_id', 'whatsapp_templates', ['family_id'])
    op.create_index('ix_whatsapp_templates_family_status', 'whatsapp_templates', ['family_id', 'status'])
    op.create_index(
        'ix_whatsapp_templates_name_lang_status', 'whatsapp_templates',
        ['template_name', 'language', 'status'],
    )

    op.add_column('email_sync_state', sa.Column('last_error', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('email_sync_state', 'last_error')

    op.drop_index('ix_whatsapp_templates_name_lang_status', table_name='whatsapp_templates')
    op.drop_index('ix_whatsapp_templates_family_status', table_name='whatsapp_templates')
    op.drop_index('ix_whatsapp_templates_family_id', table_name='whatsapp_templates')

    op.drop_column('whatsapp_templates', 'last_used_at')
    op.drop_column('whatsapp_templates', 'usage_count')
    op.drop_column('whatsapp_templates', 'rejection_reason')
    op.drop_column('whatsapp_templates', 'quality_rating')
    op.drop_column('whatsapp_templates', 'version')
    op.drop_column('whatsapp_templates', 'family_id')
    op.drop_column('whatsapp_templates', 'examples')
    op.drop_column('whatsapp_templates', 'header_media_url')
    op.drop_column('whatsapp_templates', 'header_text')

    # NOTE: this will fail if any family now has >1 row sharing
    # (template_name, language) — i.e. if version history has actually been
    # used since this migration ran — or if any row is still a DRAFT with
    # provider_template_id still NULL (never submitted to Meta). Both are
    # inherent to reverting this feature after it's been used, not a
    # migration bug; Postgres runs each migration in a transaction, so a
    # failure here leaves the schema exactly as it was at head, not
    # half-migrated (confirmed while authoring this migration).
    op.alter_column('whatsapp_templates', 'provider_template_id', nullable=False)
    op.create_index(
        'uq_whatsapp_templates_name_language', 'whatsapp_templates',
        ['template_name', 'language'], unique=True,
    )
