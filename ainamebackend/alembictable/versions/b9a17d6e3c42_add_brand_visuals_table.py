"""add brand visuals table

Revision ID: b9a17d6e3c42
Revises: 8b7c2d4f9a10
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b9a17d6e3c42"
down_revision: Union[str, None] = "8b7c2d4f9a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brand_visuals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("moral", sa.Text(), nullable=True),
        sa.Column("design_style", sa.String(length=100), server_default="现代极简商业风", nullable=False),
        sa.Column("slogan", sa.String(length=255), nullable=True),
        sa.Column("prompt_used", sa.Text(), nullable=True),
        sa.Column("task_id", sa.String(length=100), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_brand_visuals_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brand_visuals")),
    )
    op.create_index(op.f("ix_brand_visuals_user_id"), "brand_visuals", ["user_id"], unique=False)
    op.create_index(op.f("ix_brand_visuals_thread_id"), "brand_visuals", ["thread_id"], unique=False)
    op.create_index(op.f("ix_brand_visuals_task_id"), "brand_visuals", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_constraint(op.f("fk_brand_visuals_user_id_user"), "brand_visuals", type_="foreignkey")
    op.drop_index(op.f("ix_brand_visuals_task_id"), table_name="brand_visuals")
    op.drop_index(op.f("ix_brand_visuals_thread_id"), table_name="brand_visuals")
    op.drop_index(op.f("ix_brand_visuals_user_id"), table_name="brand_visuals")
    op.drop_table("brand_visuals")
