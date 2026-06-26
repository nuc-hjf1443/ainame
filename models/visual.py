from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class BrandKit(Base):
    __tablename__ = "brand_kits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    naming_asset_id: Mapped[int | None] = mapped_column(ForeignKey("naming_assets.id"), nullable=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(100))
    moral: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str] = mapped_column(String(200))
    audience: Mapped[str] = mapped_column(String(200))
    design_style: Mapped[str] = mapped_column(String(100), default="现代简约", server_default="现代简约")
    primary_color: Mapped[str] = mapped_column(String(50), default="蓝色", server_default="蓝色")
    image_model: Mapped[str] = mapped_column(String(100), default="wan2.6-image", server_default="wan2.6-image")
    slogan: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", server_default="PENDING", index=True)
    quota_refunded: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    quota_usage_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class BrandVisual(Base):
    __tablename__ = "brand_visuals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    brand_kit_id: Mapped[int | None] = mapped_column(ForeignKey("brand_kits.id"), nullable=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    moral: Mapped[str | None] = mapped_column(Text, nullable=True)
    design_style: Mapped[str] = mapped_column(String(100), default="现代极简商业风", server_default="现代极简商业风")
    image_model: Mapped[str] = mapped_column(String(100), default="wan2.6-image", server_default="wan2.6-image")
    asset_type: Mapped[str] = mapped_column(String(30), default="LOGO", server_default="LOGO")
    variant_index: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    slogan: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    quota_refunded: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    quota_usage_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", server_default="PENDING")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
