"""add expert chat attachments

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expert_chat_attachments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("uploader_user_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=True),
        sa.Column("file_size", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["thread_id"], ["expert_chat_threads.id"], name=op.f("fk_expert_chat_attachments_thread_id_expert_chat_threads")),
        sa.ForeignKeyConstraint(["message_id"], ["expert_chat_messages.id"], name=op.f("fk_expert_chat_attachments_message_id_expert_chat_messages")),
        sa.ForeignKeyConstraint(["uploader_user_id"], ["user.id"], name=op.f("fk_expert_chat_attachments_uploader_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_chat_attachments")),
    )
    op.create_index(op.f("ix_expert_chat_attachments_thread_id"), "expert_chat_attachments", ["thread_id"], unique=False)
    op.create_index(op.f("ix_expert_chat_attachments_message_id"), "expert_chat_attachments", ["message_id"], unique=False)
    op.create_index(op.f("ix_expert_chat_attachments_uploader_user_id"), "expert_chat_attachments", ["uploader_user_id"], unique=False)
    op.create_index(op.f("ix_expert_chat_attachments_created_time"), "expert_chat_attachments", ["created_time"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_expert_chat_attachments_created_time"), table_name="expert_chat_attachments")
    op.drop_index(op.f("ix_expert_chat_attachments_uploader_user_id"), table_name="expert_chat_attachments")
    op.drop_index(op.f("ix_expert_chat_attachments_message_id"), table_name="expert_chat_attachments")
    op.drop_index(op.f("ix_expert_chat_attachments_thread_id"), table_name="expert_chat_attachments")
    op.drop_table("expert_chat_attachments")
