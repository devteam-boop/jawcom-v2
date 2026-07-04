"""Change flow_execution_logs lead_id from UUID to BIGINT

Revision ID: aab231fef80b
Revises: c5d48d6b0da6
Create Date: 2026-07-03 16:37:32.098269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aab231fef80b'
down_revision: Union[str, Sequence[str], None] = 'c5d48d6b0da6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_flow_execution_logs_lead_id',
                  table_name='flow_execution_logs')
    op.alter_column('flow_execution_logs', 'lead_id',
                    type_=sa.BigInteger(),
                    postgresql_using='lead_id::text::bigint',
                    existing_nullable=False)
    op.create_index('ix_flow_execution_logs_lead_id',
                    'flow_execution_logs', ['lead_id'])


def downgrade() -> None:
    op.drop_index('ix_flow_execution_logs_lead_id',
                  table_name='flow_execution_logs')
    op.alter_column('flow_execution_logs', 'lead_id',
                    type_=sa.UUID(),
                    postgresql_using='lead_id::text::uuid',
                    existing_nullable=False)
    op.create_index('ix_flow_execution_logs_lead_id',
                    'flow_execution_logs', ['lead_id'])
