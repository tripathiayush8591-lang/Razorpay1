"""phase6_fulfillment_and_tracking

Revision ID: 0003_phase6_fulfillment
Revises: 3fd202bc5023
Create Date: 2026-09-03 10:48:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_phase6_fulfillment'
down_revision: Union[str, None] = '3fd202bc5023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('merchant_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('processing_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('shipped_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('delivered_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('cancelled_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('cancellation_reason', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('carrier', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('tracking_number', sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('merchant_orders', schema=None) as batch_op:
        batch_op.drop_column('tracking_number')
        batch_op.drop_column('carrier')
        batch_op.drop_column('cancellation_reason')
        batch_op.drop_column('cancelled_at')
        batch_op.drop_column('delivered_at')
        batch_op.drop_column('shipped_at')
        batch_op.drop_column('processing_at')
