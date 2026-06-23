from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    cover_visual_id: Mapped[int | None] = mapped_column(ForeignKey("brand_visuals.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", server_default="ACTIVE", index=True)
    vote_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    comment_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CommunityCandidate(Base):
    __tablename__ = "community_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"), index=True)
    source_asset_id: Mapped[int | None] = mapped_column(ForeignKey("naming_assets.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    moral: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    vote_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class CommunityVote(Base):
    __tablename__ = "community_votes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_community_vote_post_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("community_candidates.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CommunityComment(Base):
    __tablename__ = "community_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", server_default="ACTIVE")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class CommunityReport(Base):
    __tablename__ = "community_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[int] = mapped_column(Integer, index=True)
    reason: Mapped[str] = mapped_column(String(30))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", server_default="PENDING", index=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    reviewed_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
