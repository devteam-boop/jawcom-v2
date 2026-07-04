"""Add flow_definition_id FK column to journeys table

Replaces the previous name-based convention with an explicit nullable FK
pointing to flow_definitions.id.

Revision ID: c1d2e3f4a5b6
Revises: b3c4d5e6f7a8
Create Date: 2026-07-03 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add flow_definition_id to journeys as a nullable FK."""
    op.add_column(
        'journeys',
        sa.Column('flow_definition_id', UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_journeys_flow_definition_id',
        'journeys', 'flow_definitions',
        ['flow_definition_id'], ['id'],
    )


def downgrade() -> None:
    """Remove flow_definition_id column and FK."""
    op.drop_constraint(
        'fk_journeys_flow_definition_id', 'journeys', type_='foreignkey',
    )
    op.drop_column('journeys', 'flow_definition_id')
