"""Add missing FK on flow_execution_logs.running_instance_id
→ running_journey_instances.id

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-07-03 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add FK on flow_execution_logs.running_instance_id."""
    op.create_foreign_key(
        'fk_flow_execution_logs_running_instance',
        'flow_execution_logs', 'running_journey_instances',
        ['running_instance_id'], ['id'],
    )


def downgrade() -> None:
    """Drop FK on flow_execution_logs.running_instance_id."""
    op.drop_constraint(
        'fk_flow_execution_logs_running_instance',
        'flow_execution_logs',
        type_='foreignkey',
    )
