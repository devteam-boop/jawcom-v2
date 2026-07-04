"""Change running_journey_instances lead_id from UUID to BIGINT

Revision ID: c5d48d6b0da6
Revises: c1d2e3f4a5b6
Create Date: 2026-07-03 15:29:05.468575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5d48d6b0da6'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_running_journey_instances_lead_id',
                  table_name='running_journey_instances')
    op.alter_column('running_journey_instances', 'lead_id',
                    type_=sa.BigInteger(),
                    postgresql_using='lead_id::text::bigint',
                    existing_nullable=False)
    op.create_index('ix_running_journey_instances_lead_id',
                    'running_journey_instances', ['lead_id'])


def downgrade() -> None:
    op.drop_index('ix_running_journey_instances_lead_id',
                  table_name='running_journey_instances')
    op.alter_column('running_journey_instances', 'lead_id',
                    type_=sa.UUID(),
                    postgresql_using='lead_id::text::uuid',
                    existing_nullable=False)
    op.create_index('ix_running_journey_instances_lead_id',
                    'running_journey_instances', ['lead_id'])
