"""Email Template Lifecycle: add family_id to templates

Adds the same family-of-versions concept whatsapp_templates already has
(see a6b7c8d9e0f1_whatsapp_template_versioning.py) to the generic
`templates` table (email/sms/whatsapp-legacy/push), so email templates can
support Draft -> Active -> Archived with "only one ACTIVE version per
family" (app/templates/services.py TemplateService.activate_template,
channel="email" only).

family_id is backfilled with a fresh, independent UUID per existing row —
deliberately NOT the row's own id, for the identical reason documented in
a6b7c8d9e0f1: TemplateService.get_template() resolves a plain row id
before ever falling back to treating the value as a family_id, so if
family_id ever equalled a row's own id, a Journey/flow node later
configured with that family_id (to "follow the latest ACTIVE version" once
a second version exists) would always resolve to this one specific row
directly instead, silently defeating the whole mechanism.

No `status` values are touched — this is purely additive, so any
template that is already ACTIVE stays ACTIVE after this migration runs.

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-07-11 00:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a6b7c8d9e0f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('templates', sa.Column('family_id', UUID(as_uuid=True), nullable=True))

    # Per-row independent UUID via a Python loop — same approach as
    # a6b7c8d9e0f1_whatsapp_template_versioning.py, for the same reason
    # (no dependency on a specific Postgres extension for gen_random_uuid()).
    connection = op.get_bind()
    templates = sa.table(
        'templates',
        sa.column('id', UUID(as_uuid=True)),
        sa.column('family_id', UUID(as_uuid=True)),
    )
    rows = connection.execute(
        sa.select(templates.c.id).where(templates.c.family_id.is_(None))
    ).fetchall()
    for (row_id,) in rows:
        connection.execute(
            templates.update()
            .where(templates.c.id == row_id)
            .values(family_id=uuid.uuid4())
        )
    op.alter_column('templates', 'family_id', nullable=False)

    op.create_index('ix_templates_family_id', 'templates', ['family_id'])
    op.create_index('ix_templates_family_status', 'templates', ['family_id', 'status'])


def downgrade() -> None:
    op.drop_index('ix_templates_family_status', table_name='templates')
    op.drop_index('ix_templates_family_id', table_name='templates')
    op.drop_column('templates', 'family_id')
