from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.asset import NamingAsset
from models.community import CommunityCandidate, CommunityComment, CommunityPost, CommunityReport, CommunityVote
from models.user import User
from models.visual import BrandVisual


class CommunityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_post(self, user_id: int, values: dict, candidates: list[dict]):
        cover_id = values.get("cover_visual_id")
        if cover_id:
            visual = await self.session.scalar(select(BrandVisual).where(BrandVisual.id == cover_id, BrandVisual.user_id == user_id, BrandVisual.status == "SUCCESS"))
            if not visual:
                raise ValueError("封面视觉资产不存在")
        for candidate in candidates:
            asset_id = candidate.get("source_asset_id")
            if asset_id and not await self.session.scalar(select(NamingAsset.id).where(NamingAsset.id == asset_id, NamingAsset.user_id == user_id)):
                raise ValueError("候选名字资产不存在")
        post = CommunityPost(author_id=user_id, **values)
        self.session.add(post)
        await self.session.flush()
        self.session.add_all(CommunityCandidate(post_id=post.id, **item) for item in candidates)
        await self.session.commit()
        return post

    async def _post_payload(self, post: CommunityPost, user_id: int | None):
        author = await self.session.get(User, post.author_id)
        candidates = (await self.session.execute(select(CommunityCandidate).where(CommunityCandidate.post_id == post.id).order_by(CommunityCandidate.id))).scalars().all()
        cover_url = None
        if post.cover_visual_id:
            visual = await self.session.get(BrandVisual, post.cover_visual_id)
            cover_url = visual.image_url if visual else None
        my_vote = None
        if user_id:
            vote = await self.session.scalar(select(CommunityVote).where(CommunityVote.post_id == post.id, CommunityVote.user_id == user_id))
            my_vote = vote.candidate_id if vote else None
        return {
            "id": post.id, "author_id": post.author_id, "author_name": author.username if author else "用户",
            "title": post.title, "description": post.description, "category": post.category,
            "cover_image_url": cover_url, "vote_count": post.vote_count, "comment_count": post.comment_count,
            "candidates": candidates, "my_vote_candidate_id": my_vote, "created_time": post.created_time,
        }

    async def list_posts(self, page: int, page_size: int, sort: str, category: str | None, user_id: int | None):
        conditions = [CommunityPost.status == "ACTIVE"]
        if category:
            conditions.append(CommunityPost.category == category)
        total = await self.session.scalar(select(func.count()).select_from(CommunityPost).where(*conditions)) or 0
        order = CommunityPost.vote_count.desc() if sort == "popular" else CommunityPost.created_time.desc()
        posts = (await self.session.execute(select(CommunityPost).where(*conditions).order_by(order, CommunityPost.id.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return [await self._post_payload(post, user_id) for post in posts], total

    async def get_post(self, post_id: int, user_id: int | None, include_hidden: bool = False):
        conditions = [CommunityPost.id == post_id]
        if not include_hidden:
            conditions.append(CommunityPost.status == "ACTIVE")
        post = await self.session.scalar(select(CommunityPost).where(*conditions))
        return await self._post_payload(post, user_id) if post else None

    async def vote(self, post_id: int, candidate_id: int, user_id: int):
        post = await self.session.scalar(
            select(CommunityPost)
            .where(CommunityPost.id == post_id, CommunityPost.status == "ACTIVE")
            .with_for_update()
        )
        candidate = await self.session.scalar(
            select(CommunityCandidate)
            .where(CommunityCandidate.id == candidate_id, CommunityCandidate.post_id == post_id)
            .with_for_update()
        )
        if not post or not candidate:
            return None
        vote = await self.session.scalar(
            select(CommunityVote)
            .where(CommunityVote.post_id == post_id, CommunityVote.user_id == user_id)
            .with_for_update()
        )
        if vote and vote.candidate_id == candidate_id:
            return post
        if vote:
            old = await self.session.scalar(
                select(CommunityCandidate)
                .where(CommunityCandidate.id == vote.candidate_id)
                .with_for_update()
            )
            if old:
                old.vote_count = max(0, old.vote_count - 1)
            vote.candidate_id = candidate_id
        else:
            self.session.add(CommunityVote(post_id=post_id, candidate_id=candidate_id, user_id=user_id))
            post.vote_count += 1
        candidate.vote_count += 1
        await self.session.commit()
        return post

    async def remove_vote(self, post_id: int, user_id: int):
        post = await self.session.scalar(
            select(CommunityPost).where(CommunityPost.id == post_id).with_for_update()
        )
        vote = await self.session.scalar(
            select(CommunityVote)
            .where(CommunityVote.post_id == post_id, CommunityVote.user_id == user_id)
            .with_for_update()
        )
        if not vote:
            return False
        candidate = await self.session.scalar(
            select(CommunityCandidate)
            .where(CommunityCandidate.id == vote.candidate_id)
            .with_for_update()
        )
        if post:
            post.vote_count = max(0, post.vote_count - 1)
        if candidate:
            candidate.vote_count = max(0, candidate.vote_count - 1)
        await self.session.delete(vote)
        await self.session.commit()
        return True

    async def add_comment(self, post_id: int, user_id: int, content: str):
        post = await self.session.scalar(select(CommunityPost).where(CommunityPost.id == post_id, CommunityPost.status == "ACTIVE"))
        if not post:
            return None
        comment = CommunityComment(post_id=post_id, user_id=user_id, content=content)
        post.comment_count += 1
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def list_comments(self, post_id: int, page: int, page_size: int):
        active_post = await self.session.scalar(
            select(CommunityPost.id).where(
                CommunityPost.id == post_id,
                CommunityPost.status == "ACTIVE",
            )
        )
        if not active_post:
            return [], 0
        where = (CommunityComment.post_id == post_id, CommunityComment.status == "ACTIVE")
        total = await self.session.scalar(select(func.count()).select_from(CommunityComment).where(*where)) or 0
        rows = (await self.session.execute(select(CommunityComment, User.username).join(User, User.id == CommunityComment.user_id).where(*where).order_by(CommunityComment.id.desc()).offset((page - 1) * page_size).limit(page_size))).all()
        return [{"id": c.id, "post_id": c.post_id, "user_id": c.user_id, "username": username, "content": c.content, "created_time": c.created_time} for c, username in rows], total

    async def soft_delete_post(self, post_id: int, user_id: int):
        post = await self.session.scalar(select(CommunityPost).where(CommunityPost.id == post_id, CommunityPost.author_id == user_id))
        if not post:
            return False
        post.status = "DELETED"
        await self.session.commit()
        return True

    async def soft_delete_comment(self, comment_id: int, user_id: int):
        comment = await self.session.scalar(select(CommunityComment).where(CommunityComment.id == comment_id, CommunityComment.user_id == user_id, CommunityComment.status == "ACTIVE"))
        if not comment:
            return False
        comment.status = "DELETED"
        post = await self.session.get(CommunityPost, comment.post_id)
        if post:
            post.comment_count = max(0, post.comment_count - 1)
        await self.session.commit()
        return True

    async def report(self, user_id: int, values: dict):
        target_type, target_id = values["target_type"], values["target_id"]
        target_model = CommunityPost if target_type == "POST" else CommunityComment
        target = await self.session.get(target_model, target_id)
        if not target or target.status != "ACTIVE":
            return None
        report = CommunityReport(reporter_id=user_id, **values)
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def list_reports(self, page: int, page_size: int, status: str | None = None):
        conditions = [] if not status else [CommunityReport.status == status]
        total = await self.session.scalar(select(func.count()).select_from(CommunityReport).where(*conditions)) or 0
        result = await self.session.execute(select(CommunityReport).where(*conditions).order_by(CommunityReport.id.desc()).offset((page - 1) * page_size).limit(page_size))
        return result.scalars().all(), total

    async def moderate_report(self, report_id: int, admin_id: int, action: str, resolution: str | None):
        report = await self.session.get(CommunityReport, report_id)
        if not report or report.status != "PENDING":
            return None
        if action == "HIDE":
            if report.target_type == "POST":
                target = await self.session.get(CommunityPost, report.target_id)
            else:
                target = await self.session.get(CommunityComment, report.target_id)
            if target:
                target.status = "HIDDEN"
        report.status = "RESOLVED" if action == "HIDE" else "DISMISSED"
        report.resolution, report.reviewed_by, report.reviewed_time = resolution, admin_id, datetime.now()
        await self.session.commit()
        await self.session.refresh(report)
        return report
