"""add expert chat wallet

Revision ID: a7b8c9d0e1f2
Revises: c3d4e5f6a7b8
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expert_chat_threads",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("service_order_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="OPEN", nullable=False),
        sa.Column("customer_unread_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expert_unread_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.Column("updated_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["user.id"], name=op.f("fk_expert_chat_threads_customer_id_user")),
        sa.ForeignKeyConstraint(["expert_id"], ["expert_profiles.id"], name=op.f("fk_expert_chat_threads_expert_id_expert_profiles")),
        sa.ForeignKeyConstraint(["package_id"], ["expert_service_packages.id"], name=op.f("fk_expert_chat_threads_package_id_expert_service_packages")),
        sa.ForeignKeyConstraint(["service_order_id"], ["expert_service_orders.id"], name=op.f("fk_expert_chat_threads_service_order_id_expert_service_orders")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_chat_threads")),
    )
    op.create_index(op.f("ix_expert_chat_threads_customer_id"), "expert_chat_threads", ["customer_id"], unique=False)
    op.create_index(op.f("ix_expert_chat_threads_expert_id"), "expert_chat_threads", ["expert_id"], unique=False)
    op.create_index(op.f("ix_expert_chat_threads_package_id"), "expert_chat_threads", ["package_id"], unique=False)
    op.create_index(op.f("ix_expert_chat_threads_service_order_id"), "expert_chat_threads", ["service_order_id"], unique=False)
    op.create_index(op.f("ix_expert_chat_threads_status"), "expert_chat_threads", ["status"], unique=False)
    op.create_index(op.f("ix_expert_chat_threads_last_message_at"), "expert_chat_threads", ["last_message_at"], unique=False)

    op.create_table(
        "expert_chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("sender_user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("read_time", sa.DateTime(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["thread_id"], ["expert_chat_threads.id"], name=op.f("fk_expert_chat_messages_thread_id_expert_chat_threads")),
        sa.ForeignKeyConstraint(["sender_user_id"], ["user.id"], name=op.f("fk_expert_chat_messages_sender_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_chat_messages")),
    )
    op.create_index(op.f("ix_expert_chat_messages_thread_id"), "expert_chat_messages", ["thread_id"], unique=False)
    op.create_index(op.f("ix_expert_chat_messages_sender_user_id"), "expert_chat_messages", ["sender_user_id"], unique=False)
    op.create_index(op.f("ix_expert_chat_messages_created_time"), "expert_chat_messages", ["created_time"], unique=False)

    op.create_table(
        "expert_wallets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("available_balance", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("withdrawing_balance", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("total_income", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("total_withdrawn", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.Column("updated_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["expert_id"], ["expert_profiles.id"], name=op.f("fk_expert_wallets_expert_id_expert_profiles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_wallets")),
        sa.UniqueConstraint("expert_id", name=op.f("uq_expert_wallets_expert_id")),
    )
    op.create_index(op.f("ix_expert_wallets_expert_id"), "expert_wallets", ["expert_id"], unique=False)

    op.create_table(
        "expert_withdrawals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("alipay_account", sa.String(length=100), nullable=False),
        sa.Column("real_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_time", sa.DateTime(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.Column("updated_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["wallet_id"], ["expert_wallets.id"], name=op.f("fk_expert_withdrawals_wallet_id_expert_wallets")),
        sa.ForeignKeyConstraint(["expert_id"], ["expert_profiles.id"], name=op.f("fk_expert_withdrawals_expert_id_expert_profiles")),
        sa.ForeignKeyConstraint(["reviewed_by"], ["user.id"], name=op.f("fk_expert_withdrawals_reviewed_by_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_withdrawals")),
    )
    op.create_index(op.f("ix_expert_withdrawals_wallet_id"), "expert_withdrawals", ["wallet_id"], unique=False)
    op.create_index(op.f("ix_expert_withdrawals_expert_id"), "expert_withdrawals", ["expert_id"], unique=False)
    op.create_index(op.f("ix_expert_withdrawals_status"), "expert_withdrawals", ["status"], unique=False)

    op.create_table(
        "expert_wallet_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("service_order_id", sa.Integer(), nullable=True),
        sa.Column("withdrawal_id", sa.Integer(), nullable=True),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(10, 2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["wallet_id"], ["expert_wallets.id"], name=op.f("fk_expert_wallet_transactions_wallet_id_expert_wallets")),
        sa.ForeignKeyConstraint(["expert_id"], ["expert_profiles.id"], name=op.f("fk_expert_wallet_transactions_expert_id_expert_profiles")),
        sa.ForeignKeyConstraint(["service_order_id"], ["expert_service_orders.id"], name=op.f("fk_expert_wallet_transactions_service_order_id_expert_service_orders")),
        sa.ForeignKeyConstraint(["withdrawal_id"], ["expert_withdrawals.id"], name=op.f("fk_expert_wallet_transactions_withdrawal_id_expert_withdrawals")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_wallet_transactions")),
        sa.UniqueConstraint("transaction_type", "service_order_id", name="uq_wallet_tx_type_service_order"),
    )
    op.create_index(op.f("ix_expert_wallet_transactions_wallet_id"), "expert_wallet_transactions", ["wallet_id"], unique=False)
    op.create_index(op.f("ix_expert_wallet_transactions_expert_id"), "expert_wallet_transactions", ["expert_id"], unique=False)
    op.create_index(op.f("ix_expert_wallet_transactions_service_order_id"), "expert_wallet_transactions", ["service_order_id"], unique=False)
    op.create_index(op.f("ix_expert_wallet_transactions_withdrawal_id"), "expert_wallet_transactions", ["withdrawal_id"], unique=False)
    op.create_index(op.f("ix_expert_wallet_transactions_transaction_type"), "expert_wallet_transactions", ["transaction_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_expert_wallet_transactions_transaction_type"), table_name="expert_wallet_transactions")
    op.drop_index(op.f("ix_expert_wallet_transactions_withdrawal_id"), table_name="expert_wallet_transactions")
    op.drop_index(op.f("ix_expert_wallet_transactions_service_order_id"), table_name="expert_wallet_transactions")
    op.drop_index(op.f("ix_expert_wallet_transactions_expert_id"), table_name="expert_wallet_transactions")
    op.drop_index(op.f("ix_expert_wallet_transactions_wallet_id"), table_name="expert_wallet_transactions")
    op.drop_table("expert_wallet_transactions")
    op.drop_index(op.f("ix_expert_withdrawals_status"), table_name="expert_withdrawals")
    op.drop_index(op.f("ix_expert_withdrawals_expert_id"), table_name="expert_withdrawals")
    op.drop_index(op.f("ix_expert_withdrawals_wallet_id"), table_name="expert_withdrawals")
    op.drop_table("expert_withdrawals")
    op.drop_index(op.f("ix_expert_wallets_expert_id"), table_name="expert_wallets")
    op.drop_table("expert_wallets")
    op.drop_index(op.f("ix_expert_chat_messages_created_time"), table_name="expert_chat_messages")
    op.drop_index(op.f("ix_expert_chat_messages_sender_user_id"), table_name="expert_chat_messages")
    op.drop_index(op.f("ix_expert_chat_messages_thread_id"), table_name="expert_chat_messages")
    op.drop_table("expert_chat_messages")
    op.drop_index(op.f("ix_expert_chat_threads_last_message_at"), table_name="expert_chat_threads")
    op.drop_index(op.f("ix_expert_chat_threads_status"), table_name="expert_chat_threads")
    op.drop_index(op.f("ix_expert_chat_threads_service_order_id"), table_name="expert_chat_threads")
    op.drop_index(op.f("ix_expert_chat_threads_package_id"), table_name="expert_chat_threads")
    op.drop_index(op.f("ix_expert_chat_threads_expert_id"), table_name="expert_chat_threads")
    op.drop_index(op.f("ix_expert_chat_threads_customer_id"), table_name="expert_chat_threads")
    op.drop_table("expert_chat_threads")
