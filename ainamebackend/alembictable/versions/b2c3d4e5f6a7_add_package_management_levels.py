"""add package management levels

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-02 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("package_config", sa.Column("package_type", sa.String(length=30), nullable=True))
    op.create_index(op.f("ix_package_config_package_type"), "package_config", ["package_type"], unique=False)
    op.execute("UPDATE package_config SET package_type = 'VIP' WHERE package_code IN ('VIP_MONTHLY', 'VIP_YEARLY')")
    op.execute("UPDATE package_config SET package_type = 'NAMING_QUOTA' WHERE package_code LIKE 'QUOTA_NAMING_%'")

    op.add_column(
        "expert_profiles",
        sa.Column("expert_level", sa.String(length=20), server_default="STANDARD", nullable=False),
    )
    op.create_index(op.f("ix_expert_profiles_expert_level"), "expert_profiles", ["expert_level"], unique=False)

    op.add_column(
        "expert_service_packages",
        sa.Column("expert_level", sa.String(length=20), server_default="STANDARD", nullable=False),
    )
    op.create_index(
        op.f("ix_expert_service_packages_expert_level"),
        "expert_service_packages",
        ["expert_level"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_expert_service_packages_expert_level"), table_name="expert_service_packages")
    op.drop_column("expert_service_packages", "expert_level")
    op.drop_index(op.f("ix_expert_profiles_expert_level"), table_name="expert_profiles")
    op.drop_column("expert_profiles", "expert_level")
    op.drop_index(op.f("ix_package_config_package_type"), table_name="package_config")
    op.drop_column("package_config", "package_type")
