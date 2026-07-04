from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class PackageConfig(Base):
    __tablename__ = "package_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    package_code: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    package_type: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    api_quota: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    duration_days: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    naming_daily_quota: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    visual_daily_quota: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    expert_discount: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.00"), server_default="1.00")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", server_default="ACTIVE")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    package_id: Mapped[int | None] = mapped_column(ForeignKey("package_config.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", server_default="PENDING")
    order_type: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    payment_provider: Mapped[str] = mapped_column(String(30), default="MOCK", server_default="MOCK")
    out_trade_no: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    provider_trade_no: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    payment_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    refund_request_no: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    refunded_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class RefundAudit(Base):
    __tablename__ = "refund_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", server_default="PENDING")
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ApiBill(Base):
    __tablename__ = "api_bill"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    feature: Mapped[str] = mapped_column(String(100))
    token_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    quota_cost: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UserMembership(Base):
    __tablename__ = "user_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("package_config.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", server_default="ACTIVE")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserQuotaBalance(Base):
    __tablename__ = "user_quota_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    naming_balance: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class DailyQuotaUsage(Base):
    __tablename__ = "daily_quota_usage"
    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="uq_daily_quota_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    usage_date: Mapped[date] = mapped_column(Date, index=True)
    naming_used: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    visual_used: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
