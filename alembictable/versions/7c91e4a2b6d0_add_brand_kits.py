"""add brand kits

Revision ID: 7c91e4a2b6d0
Revises: 0bb0a0fc0772
Create Date: 2026-06-23 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c91e4a2b6d0"
down_revision: Union[str, None] = "0bb0a0fc0772"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brand_kits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("moral", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(length=200), nullable=False),
        sa.Column("audience", sa.String(length=200), nullable=False),
        sa.Column("design_style", sa.String(length=100), server_default="现代简约", nullable=False),
        sa.Column("primary_color", sa.String(length=50), server_default="蓝色", nullable=False),
        sa.Column("image_model", sa.String(length=100), server_default="wan2.6-image", nullable=False),
        sa.Column("slogan", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_brand_kits_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brand_kits")),
    )
    op.create_index(op.f("ix_brand_kits_user_id"), "brand_kits", ["user_id"], unique=False)
    op.create_index(op.f("ix_brand_kits_thread_id"), "brand_kits", ["thread_id"], unique=False)
    op.create_index(op.f("ix_brand_kits_status"), "brand_kits", ["status"], unique=False)
    op.add_column("brand_visuals", sa.Column("brand_kit_id", sa.Integer(), nullable=True))
    op.add_column("brand_visuals", sa.Column("asset_type", sa.String(length=30), server_default="LOGO", nullable=False))
    op.add_column("brand_visuals", sa.Column("variant_index", sa.Integer(), server_default="1", nullable=False))
    op.create_foreign_key(op.f("fk_brand_visuals_brand_kit_id_brand_kits"), "brand_visuals", "brand_kits", ["brand_kit_id"], ["id"])
    op.create_index(op.f("ix_brand_visuals_brand_kit_id"), "brand_visuals", ["brand_kit_id"], unique=False)


def downgrade() -> None:
    op.drop_constraint(op.f("fk_brand_visuals_brand_kit_id_brand_kits"), "brand_visuals", type_="foreignkey")
    op.drop_index(op.f("ix_brand_visuals_brand_kit_id"), table_name="brand_visuals")
    op.drop_column("brand_visuals", "variant_index")
    op.drop_column("brand_visuals", "asset_type")
    op.drop_column("brand_visuals", "brand_kit_id")
    op.drop_table("brand_kits")
