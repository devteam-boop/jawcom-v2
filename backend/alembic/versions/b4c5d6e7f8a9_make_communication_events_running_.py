"""Make communication_events.running_instance_id nullable

Allows manual (non-Journey) communication to be recorded in the same
communication_events table. running_instance_id NULL = manual send;
running_instance_id = real UUID = Journey-originated send. The FK
constraint to running_journey_instances is left in place unchanged — NULL
values are not checked by a foreign key, so Journey-originated rows keep
the same integrity guarantee as before.

Revision ID: b4c5d6e7f8a9
Revises: a1b2c3d4e5f6
Create Date: 2026-07-09 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'communication_events', 'running_instance_id',
        existing_type=UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'communication_events', 'running_instance_id',
        existing_type=UUID(as_uuid=True),
        nullable=False,
    )
