from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_current_user, get_optional_user_id, get_session
from models.user import User
from repository.community_repo import CommunityRepository
from schemas.community_schemas import CommentIn, CommentOut, CommentPageOut, CommunityPostCreateIn, CommunityPostOut, CommunityPostPageOut, ReportIn, VoteIn


router = APIRouter(prefix="/community", tags=["community"])
auth = AuthHandler()


@router.get("/posts", response_model=CommunityPostPageOut)
async def list_posts(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50), sort: str = Query("latest", pattern="^(latest|popular)$"), category: str | None = None, user_id: int | None = Depends(get_optional_user_id), session: AsyncSession = Depends(get_session)):
    items, total = await CommunityRepository(session).list_posts(page, page_size, sort, category, user_id)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/posts/{post_id}", response_model=CommunityPostOut)
async def get_post(post_id: int, user_id: int | None = Depends(get_optional_user_id), session: AsyncSession = Depends(get_session)):
    post = await CommunityRepository(session).get_post(post_id, user_id)
    if not post:
        raise HTTPException(404, detail="帖子不存在")
    return post


@router.post("/posts", response_model=CommunityPostOut)
async def create_post(data: CommunityPostCreateIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    values = data.model_dump(exclude={"candidates"})
    try:
        post = await repo.create_post(user.id, values, [item.model_dump() for item in data.candidates])
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc))
    return await repo.get_post(post.id, user.id)


@router.put("/posts/{post_id}/vote", response_model=CommunityPostOut)
async def vote(post_id: int, data: VoteIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    if not await repo.vote(post_id, data.candidate_id, user.id):
        raise HTTPException(404, detail="帖子或候选名不存在")
    return await repo.get_post(post_id, user.id)


@router.delete("/posts/{post_id}/vote")
async def remove_vote(post_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not await CommunityRepository(session).remove_vote(post_id, user.id):
        raise HTTPException(404, detail="尚未投票")
    return {"message": "已取消投票"}


@router.get("/posts/{post_id}/comments", response_model=CommentPageOut)
async def list_comments(post_id: int, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), session: AsyncSession = Depends(get_session)):
    items, total = await CommunityRepository(session).list_comments(post_id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/posts/{post_id}/comments", response_model=CommentOut)
async def add_comment(post_id: int, data: CommentIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    repo = CommunityRepository(session)
    comment = await repo.add_comment(post_id, user.id, data.content)
    if not comment:
        raise HTTPException(404, detail="帖子不存在")
    items, _ = await repo.list_comments(post_id, 1, 100)
    return next(item for item in items if item["id"] == comment.id)


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not await CommunityRepository(session).soft_delete_post(post_id, user.id):
        raise HTTPException(404, detail="帖子不存在或无权删除")
    return {"message": "帖子已删除"}


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if not await CommunityRepository(session).soft_delete_comment(comment_id, user.id):
        raise HTTPException(404, detail="评论不存在或无权删除")
    return {"message": "评论已删除"}


@router.post("/reports")
async def report_content(data: ReportIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    report = await CommunityRepository(session).report(user.id, data.model_dump())
    if not report:
        raise HTTPException(404, detail="举报目标不存在")
    return {"id": report.id, "status": report.status}
