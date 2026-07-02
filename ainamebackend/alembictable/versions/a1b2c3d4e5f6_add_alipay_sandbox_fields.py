"""add alipay sandbox fields

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-06-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("order_type", sa.String(length=30), nullable=True))
    op.add_column("orders", sa.Column("payment_provider", sa.String(length=30), server_default="MOCK", nullable=False))
    op.add_column("orders", sa.Column("out_trade_no", sa.String(length=64), nullable=True))
    op.add_column("orders", sa.Column("provider_trade_no", sa.String(length=100), nullable=True))
    op.add_column("orders", sa.Column("payment_subject", sa.String(length=255), nullable=True))
    op.add_column("orders", sa.Column("refund_request_no", sa.String(length=64), nullable=True))
    op.add_column("orders", sa.Column("refunded_time", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_orders_order_type"), "orders", ["order_type"], unique=False)
    op.create_index(op.f("ix_orders_out_trade_no"), "orders", ["out_trade_no"], unique=True)
    op.create_index(op.f("ix_orders_provider_trade_no"), "orders", ["provider_trade_no"], unique=False)
    op.create_index(op.f("ix_orders_refund_request_no"), "orders", ["refund_request_no"], unique=False)
    op.execute("UPDATE orders SET order_type = 'MEMBERSHIP' WHERE package_id IS NOT NULL")
    op.execute("UPDATE orders SET order_type = 'EXPERT_SERVICE' WHERE package_id IS NULL")


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_refund_request_no"), table_name="orders")
    op.drop_index(op.f("ix_orders_provider_trade_no"), table_name="orders")
    op.drop_index(op.f("ix_orders_out_trade_no"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_type"), table_name="orders")
    op.drop_column("orders", "refunded_time")
    op.drop_column("orders", "refund_request_no")
    op.drop_column("orders", "payment_subject")
    op.drop_column("orders", "provider_trade_no")
    op.drop_column("orders", "out_trade_no")
    op.drop_column("orders", "payment_provider")
    op.drop_column("orders", "order_type")
