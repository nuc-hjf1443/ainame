from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class NamingAsset(Base):
    __tablename__ = "naming_assets"
    __table_args__ = (UniqueConstraint("user_id", "thread_id", "name", name="uq_naming_asset_owner_thread_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    moral: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
