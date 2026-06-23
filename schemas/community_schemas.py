from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CandidateIn(BaseModel):
    source_asset_id: int | None = None
    name: str = Field(..., min_length=1, max_length=100)
    moral: str | None = Field(default=None, max_length=2000)
    reference: str | None = Field(default=None, max_length=2000)


class CandidateOut(CandidateIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vote_count: int


class CommunityPostCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=3000)
    category: Literal["人名", "企业名", "宠物名"]
    cover_visual_id: int | None = None
    candidates: list[CandidateIn] = Field(..., min_length=2, max_length=5)


class CommunityPostOut(BaseModel):
    id: int
    author_id: int
    author_name: str
    title: str
    description: str | None
    category: str
    cover_image_url: str | None
    vote_count: int
    comment_count: int
    candidates: list[CandidateOut]
    my_vote_candidate_id: int | None = None
    created_time: datetime


class CommunityPostPageOut(BaseModel):
    items: list[CommunityPostOut]
    total: int
    page: int
    page_size: int


class VoteIn(BaseModel):
    candidate_id: int


class CommentIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    username: str
    content: str
    created_time: datetime


class CommentPageOut(BaseModel):
    items: list[CommentOut]
    total: int
    page: int
    page_size: int


class ReportIn(BaseModel):
    target_type: Literal["POST", "COMMENT"]
    target_id: int
    reason: Literal["SPAM", "INAPPROPRIATE", "INFRINGEMENT", "OTHER"]
    detail: str | None = Field(default=None, max_length=1000)
