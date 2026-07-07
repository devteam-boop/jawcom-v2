"""Make templates.workspace_id nullable

Revision ID: f1a2b3c4d5e6
Revises: aab231fef80b
Create Date: 2026-07-06 00:00:00.000000

Templates are consolidated onto the `templates` table (Sprint 18 — Template
Management). The `Workspace`/`Campaign`/`Message` cluster this table's FK
points at is dormant scaffold code (not registered with any router or
service, and `Journey` has no matching side of the relationship), so there is
no live workspace to satisfy a NOT NULL constraint yet. Relaxing this column
lets templates be created today; the FK constraint itself is left in place
so workspace scoping can be enabled later with zero further schema changes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'aab231fef80b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('templates', 'workspace_id',
                     existing_type=sa.UUID(),
                     nullable=True)


def downgrade() -> None:
    op.alter_column('templates', 'workspace_id',
                     existing_type=sa.UUID(),
                     nullable=False)
