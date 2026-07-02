"""add naming quota balance

Revision ID: e4f5a6b7c8d9
Revises: d3f4a5b6c7d8
Create Date: 2026-06-25 00:00:00.000000

"""
from datetime import datetime
from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, None] = "d3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_quota_balances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("naming_balance", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_user_quota_balances_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_quota_balances")),
    )
    op.create_index(op.f("ix_user_quota_balances_user_id"), "user_quota_balances", ["user_id"], unique=True)

    package_table = sa.table(
        "package_config",
        sa.column("name", sa.String()),
        sa.column("package_code", sa.String()),
        sa.column("price", sa.Numeric()),
        sa.column("api_quota", sa.Integer()),
        sa.column("duration_days", sa.Integer()),
        sa.column("naming_daily_quota", sa.Integer()),
        sa.column("visual_daily_quota", sa.Integer()),
        sa.column("expert_discount", sa.Numeric()),
        sa.column("description", sa.Text()),
        sa.column("status", sa.String()),
        sa.column("created_time", sa.DateTime()),
        sa.column("updated_time", sa.DateTime()),
    )
    now = datetime.now()
    op.bulk_insert(package_table, [
        {
            "name": "30 次起名包", "package_code": "QUOTA_NAMING_30", "price": Decimal("9.90"),
            "api_quota": 30, "duration_days": 0, "naming_daily_quota": 0, "visual_daily_quota": 0,
            "expert_discount": Decimal("1.00"), "description": "购买后永久有效，免费/VIP 当日额度用完后自动抵扣",
            "status": "ACTIVE", "created_time": now, "updated_time": now,
        },
        {
            "name": "100 次起名包", "package_code": "QUOTA_NAMING_100", "price": Decimal("29.90"),
            "api_quota": 100, "duration_days": 0, "naming_daily_quota": 0, "visual_daily_quota": 0,
            "expert_discount": Decimal("1.00"), "description": "适合持续测试品牌名、人名和宠物名方案",
            "status": "ACTIVE", "created_time": now, "updated_time": now,
        },
        {
            "name": "300 次起名包", "package_code": "QUOTA_NAMING_300", "price": Decimal("79.90"),
            "api_quota": 300, "duration_days": 0, "naming_daily_quota": 0, "visual_daily_quota": 0,
            "expert_discount": Decimal("1.00"), "description": "高频起名与多轮微调的批量额度",
            "status": "ACTIVE", "created_time": now, "updated_time": now,
        },
    ])


def downgrade() -> None:
    op.execute("UPDATE orders SET package_id = NULL WHERE package_id IN (SELECT id FROM package_config WHERE package_code IN ('QUOTA_NAMING_30', 'QUOTA_NAMING_100', 'QUOTA_NAMING_300'))")
    op.execute("DELETE FROM package_config WHERE package_code IN ('QUOTA_NAMING_30', 'QUOTA_NAMING_100', 'QUOTA_NAMING_300')")
    op.drop_index(op.f("ix_user_quota_balances_user_id"), table_name="user_quota_balances")
    op.drop_table("user_quota_balances")
