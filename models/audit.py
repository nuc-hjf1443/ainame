from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class SensitiveWordInterception(Base):
    __tablename__ = "sensitive_word_interception"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    input_text: Mapped[str] = mapped_column(Text)
    matched_words: Mapped[str] = mapped_column(String(500))
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class AiContentPatrol(Base):
    __tablename__ = "ai_content_patrol"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    generated_content: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(20), default="PENDING", server_default="PENDING")
    is_violation: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
