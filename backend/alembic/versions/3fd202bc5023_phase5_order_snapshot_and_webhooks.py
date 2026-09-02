"""phase5_order_snapshot_and_webhooks

Revision ID: 3fd202bc5023
Revises: 0001_initial_schema
Create Date: 2026-09-03 02:22:06.652307

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fd202bc5023'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create processed_webhook_events for webhook idempotency
    op.create_table(
        'processed_webhook_events',
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('razorpay_order_id', sa.String(length=255), nullable=True),
        sa.Column('razorpay_payment_id', sa.String(length=255), nullable=True),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('event_id')
    )
    with op.batch_alter_table('processed_webhook_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_processed_webhook_events_razorpay_order_id'), ['razorpay_order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_processed_webhook_events_razorpay_payment_id'), ['razorpay_payment_id'], unique=False)

    # 2. Add items_snapshot_json to merchant_orders for immutable historical line items
    with op.batch_alter_table('merchant_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('items_snapshot_json', sa.Text(), server_default='[]', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('merchant_orders', schema=None) as batch_op:
        batch_op.drop_column('items_snapshot_json')

    with op.batch_alter_table('processed_webhook_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_processed_webhook_events_razorpay_payment_id'))
        batch_op.drop_index(batch_op.f('ix_processed_webhook_events_razorpay_order_id'))

    op.drop_table('processed_webhook_events')
