import pytest

from models.user import User
from repository.asset_repo import AssetRepository
from repository.community_repo import CommunityRepository


@pytest.mark.asyncio
async def test_single_vote_can_be_changed_and_removed(session):
    author = User(email="author@test.local", username="author", _password="test")
    voter = User(email="voter@test.local", username="voter", _password="test")
    session.add_all([author, voter])
    await session.commit()
    asset = await AssetRepository(session).create_name(author.id, {
        "thread_id": "thread", "name": "启明", "category": "企业名", "moral": "开启光明",
        "reference": None, "domain": None, "domain_status": None,
    })
    repo = CommunityRepository(session)
    post = await repo.create_post(author.id, {
        "title": "请选择名字", "description": None, "category": "企业名", "cover_visual_id": None,
    }, [
        {"source_asset_id": asset.id, "name": "启明", "moral": "开启光明", "reference": None},
        {"source_asset_id": None, "name": "知远", "moral": "志向长远", "reference": None},
    ])
    payload = await repo.get_post(post.id, voter.id)
    first, second = payload["candidates"]
    await repo.vote(post.id, first.id, voter.id)
    await repo.vote(post.id, second.id, voter.id)
    changed = await repo.get_post(post.id, voter.id)
    assert changed["vote_count"] == 1
    assert changed["my_vote_candidate_id"] == second.id
    assert changed["candidates"][0].vote_count == 0
    assert changed["candidates"][1].vote_count == 1
    assert await repo.remove_vote(post.id, voter.id)
    removed = await repo.get_post(post.id, voter.id)
    assert removed["vote_count"] == 0


@pytest.mark.asyncio
async def test_comment_report_and_moderation(session):
    author = User(email="a2@test.local", username="author", _password="test")
    commenter = User(email="v2@test.local", username="commenter", _password="test")
    admin = User(email="admin2@test.local", username="admin", _password="test", role="ADMIN")
    session.add_all([author, commenter, admin])
    await session.commit()
    repo = CommunityRepository(session)
    post = await repo.create_post(author.id, {"title": "投票", "description": None, "category": "人名", "cover_visual_id": None}, [
        {"source_asset_id": None, "name": "清和", "moral": None, "reference": None},
        {"source_asset_id": None, "name": "景行", "moral": None, "reference": None},
    ])
    comment = await repo.add_comment(post.id, commenter.id, "更喜欢景行")
    report = await repo.report(author.id, {"target_type": "COMMENT", "target_id": comment.id, "reason": "OTHER", "detail": "测试"})
    await repo.moderate_report(report.id, admin.id, "HIDE", "违规内容")
    comments, total = await repo.list_comments(post.id, 1, 20)
    assert total == 0
    assert comments == []


@pytest.mark.asyncio
async def test_hidden_post_does_not_expose_comments(session):
    author = User(email="hidden-author@test.local", username="author", _password="test")
    commenter = User(email="hidden-commenter@test.local", username="commenter", _password="test")
    session.add_all([author, commenter])
    await session.commit()
    repo = CommunityRepository(session)
    post = await repo.create_post(author.id, {
        "title": "待隐藏帖子", "description": None, "category": "企业名", "cover_visual_id": None,
    }, [
        {"source_asset_id": None, "name": "启明", "moral": None, "reference": None},
        {"source_asset_id": None, "name": "知远", "moral": None, "reference": None},
    ])
    await repo.add_comment(post.id, commenter.id, "不应继续公开")
    post.status = "HIDDEN"
    await session.commit()

    comments, total = await repo.list_comments(post.id, 1, 20)

    assert comments == []
    assert total == 0
