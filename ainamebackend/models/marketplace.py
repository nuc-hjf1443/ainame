from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ExpertProfile(Base):
    __tablename__ = "expert_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    expert_type: Mapped[str] = mapped_column(String(30), index=True)
    expert_level: Mapped[str] = mapped_column(String(20), default="STANDARD", server_default="STANDARD", index=True)
    bio: Mapped[str] = mapped_column(Text)
    credentials: Mapped[str] = mapped_column(Text)
    years_experience: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(20), default="PENDING", server_default="PENDING", index=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    reviewed_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ExpertServicePackage(Base):
    __tablename__ = "expert_service_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    expert_type: Mapped[str] = mapped_column(String(30), index=True)
    expert_level: Mapped[str] = mapped_column(String(20), default="STANDARD", server_default="STANDARD", index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    delivery_days: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", server_default="ACTIVE", index=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ExpertServiceOrder(Base):
    __tablename__ = "expert_service_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finance_order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    expert_id: Mapped[int] = mapped_column(ForeignKey("expert_profiles.id"), index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("expert_service_packages.id"))
    naming_asset_id: Mapped[int] = mapped_column(ForeignKey("naming_assets.id"))
    original_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.00"), server_default="1.00")
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    requirements: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_PAYMENT", server_default="PENDING_PAYMENT", index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ExpertReport(Base):
    __tablename__ = "expert_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_order_id: Mapped[int] = mapped_column(ForeignKey("expert_service_orders.id"), unique=True)
    overview: Mapped[str] = mapped_column(Text, default="")
    professional_analysis: Mapped[str] = mapped_column(Text, default="")
    phonetic_semantic_analysis: Mapped[str] = mapped_column(Text, default="")
    communication_advantages: Mapped[str] = mapped_column(Text, default="")
    risk_notes: Mapped[str] = mapped_column(Text, default="")
    recommendations: Mapped[str] = mapped_column(Text, default="")
    conclusion: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", server_default="DRAFT")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ExpertReview(Base):
    __tablename__ = "expert_reviews"
    __table_args__ = (UniqueConstraint("service_order_id", name="uq_expert_review_service_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_order_id: Mapped[int] = mapped_column(ForeignKey("expert_service_orders.id"))
    expert_id: Mapped[int] = mapped_column(ForeignKey("expert_profiles.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    rating: Mapped[int] = mapped_column(Integer)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ExpertChatThread(Base):
    __tablename__ = "expert_chat_threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    expert_id: Mapped[int] = mapped_column(ForeignKey("expert_profiles.id"), index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("expert_service_packages.id"), index=True)
    service_order_id: Mapped[int | None] = mapped_column(ForeignKey("expert_service_orders.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", server_default="OPEN", index=True)
    customer_unread_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    expert_unread_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ExpertChatMessage(Base):
    __tablename__ = "expert_chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("expert_chat_threads.id"), index=True)
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    read_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class ExpertChatAttachment(Base):
    __tablename__ = "expert_chat_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("expert_chat_threads.id"), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("expert_chat_messages.id"), nullable=True, index=True)
    uploader_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class ExpertWallet(Base):
    __tablename__ = "expert_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expert_id: Mapped[int] = mapped_column(ForeignKey("expert_profiles.id"), unique=True, index=True)
    available_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), server_default="0.00")
    withdrawing_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), server_default="0.00")
    total_income: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), server_default="0.00")
    total_withdrawn: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), server_default="0.00")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ExpertWalletTransaction(Base):
    __tablename__ = "expert_wallet_transactions"
    __table_args__ = (UniqueConstraint("transaction_type", "service_order_id", name="uq_wallet_tx_type_service_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("expert_wallets.id"), index=True)
    expert_id: Mapped[int] = mapped_column(ForeignKey("expert_profiles.id"), index=True)
    service_order_id: Mapped[int | None] = mapped_column(ForeignKey("expert_service_orders.id"), nullable=True, index=True)
    withdrawal_id: Mapped[int | None] = mapped_column(ForeignKey("expert_withdrawals.id"), nullable=True, index=True)
    transaction_type: Mapped[str] = mapped_column(String(30), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ExpertWithdrawal(Base):
    __tablename__ = "expert_withdrawals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("expert_wallets.id"), index=True)
    expert_id: Mapped[int] = mapped_column(ForeignKey("expert_profiles.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    alipay_account: Mapped[str] = mapped_column(String(100))
    real_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", server_default="PENDING", index=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    reviewed_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
