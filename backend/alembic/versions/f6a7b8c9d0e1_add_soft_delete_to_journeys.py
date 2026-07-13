"""Add soft-delete columns (deleted_at, deleted_by) to journeys

Journey deletion must never cascade to running instances, stage mappings,
execution logs, or communication events, so deletes are now soft: rows are
flagged rather than removed. Repository queries filter out flagged rows.

Revision ID: f6a7b8c9d0e1
Revises: d9e0f1a2b3c4
Create Date: 2026-07-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'd9e0f1a2b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('journeys', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('journeys', sa.Column('deleted_by', sa.String(length=255), nullable=True))
    op.create_index('ix_journeys_deleted_at', 'journeys', ['deleted_at'])


def downgrade() -> None:
    op.drop_index('ix_journeys_deleted_at', table_name='journeys')
    op.drop_column('journeys', 'deleted_by')
    op.drop_column('journeys', 'deleted_at')
