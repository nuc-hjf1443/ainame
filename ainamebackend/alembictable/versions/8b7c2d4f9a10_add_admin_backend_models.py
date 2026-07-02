"""add admin backend models

Revision ID: 8b7c2d4f9a10
Revises: 32171e181521
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b7c2d4f9a10"
down_revision: Union[str, None] = "32171e181521"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("role", sa.String(length=20), server_default="C_END", nullable=False),
    )
    op.add_column(
        "user",
        sa.Column("is_banned", sa.Boolean(), server_default=sa.text("0"), nullable=False),
    )

    op.create_table(
        "package_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("api_quota", sa.Integer(), server_default="0", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_package_config")),
    )
    op.create_table(
        "agent_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_key", sa.String(length=100), nullable=False),
        sa.Column("agent_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=100), server_default="deepseek-chat", nullable=False),
        sa.Column("temperature", sa.Numeric(precision=3, scale=2), server_default="0.50", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_config")),
        sa.UniqueConstraint("agent_key", name=op.f("uq_agent_config_agent_key")),
    )
    op.create_table(
        "knowledge_base",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_base")),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("paid_time", sa.DateTime(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["package_config.id"], name=op.f("fk_orders_package_id_package_config")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_orders_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
    )
    op.create_table(
        "api_bill",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("feature", sa.String(length=100), nullable=False),
        sa.Column("token_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("quota_cost", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_api_bill_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_bill")),
    )
    op.create_table(
        "refund_audit",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_time", sa.DateTime(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], name=op.f("fk_refund_audit_order_id_orders")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refund_audit")),
    )
    op.create_table(
        "sensitive_word_interception",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("matched_words", sa.String(length=500), nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_sensitive_word_interception_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sensitive_word_interception")),
    )
    op.create_table(
        "ai_content_patrol",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("generated_content", sa.Text(), nullable=False),
        sa.Column("review_status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("is_violation", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_ai_content_patrol_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_content_patrol")),
    )


def downgrade() -> None:
    op.drop_table("ai_content_patrol")
    op.drop_table("sensitive_word_interception")
    op.drop_table("refund_audit")
    op.drop_table("api_bill")
    op.drop_table("orders")
    op.drop_table("knowledge_base")
    op.drop_table("agent_config")
    op.drop_table("package_config")
    op.drop_column("user", "is_banned")
    op.drop_column("user", "role")
