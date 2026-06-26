"""add brand kit naming asset

Revision ID: f6a7b8c9d0e1
Revises: e4f5a6b7c8d9
Create Date: 2026-06-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("brand_kits", sa.Column("naming_asset_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_brand_kits_naming_asset_id"), "brand_kits", ["naming_asset_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_brand_kits_naming_asset_id_naming_assets"),
        "brand_kits",
        "naming_assets",
        ["naming_asset_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_brand_kits_naming_asset_id_naming_assets"), "brand_kits", type_="foreignkey")
    op.drop_index(op.f("ix_brand_kits_naming_asset_id"), table_name="brand_kits")
    op.drop_column("brand_kits", "naming_asset_id")
