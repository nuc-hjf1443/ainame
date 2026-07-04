"""update vip quota descriptions

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-03 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE package_config SET description = '每月100次智能起名、20次品牌生成，专家服务9折' "
        "WHERE package_code IN ('VIP_MONTHLY', 'VIP_YEARLY')"
    )
    op.execute(
        "UPDATE package_config SET description = REPLACE(description, '免费/VIP 当日额度用完后自动抵扣', '账号/VIP 起名额度用完后自动抵扣') "
        "WHERE package_code LIKE 'QUOTA_NAMING_%'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE package_config SET description = '每日100次智能起名、20次视觉生成，专家服务9折' "
        "WHERE package_code IN ('VIP_MONTHLY', 'VIP_YEARLY')"
    )
    op.execute(
        "UPDATE package_config SET description = REPLACE(description, '账号/VIP 起名额度用完后自动抵扣', '免费/VIP 当日额度用完后自动抵扣') "
        "WHERE package_code LIKE 'QUOTA_NAMING_%'"
    )
