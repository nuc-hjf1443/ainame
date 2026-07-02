from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.name_schemas import NameIn, NameOutSchema
# from core.nametools import generate_names
from core.workflow import generate_naming, generate_naming_v2
from core.auth import AuthHandler
from core.quota_service import refund_quota, reserve_quota
from dependencies import get_current_user, get_session
from models.user import User

auth_handler = AuthHandler()
router = APIRouter(prefix="/names", tags=["names"])


@router.post("/get_names", response_model=NameOutSchema)
async def get_names(name_info: NameIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    quota_usage_date = await reserve_quota(session, user.id, "NAMING")
    try:
        result = await generate_naming(name_info, user.id)
        return NameOutSchema(names=result["names"])
    except Exception:
        await refund_quota(session, user.id, "NAMING", quota_usage_date)
        raise


from schemas.name_schemas import NameSchemaWithThreadOut


@router.post("/generate", response_model=NameSchemaWithThreadOut)
async def get_names(name_info: NameIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # user_id 是用户创建数据库表的时候用户，当时创用id指定表明，现在查应该用相同的名字才可以
    quota_usage_date = await reserve_quota(session, user.id, "NAMING")
    try:
        result = await generate_naming_v2(name_info, user.id)
        return NameSchemaWithThreadOut(thread_id=result["thread_id"], names=result["names"]["names"])
    except Exception:
        await refund_quota(session, user.id, "NAMING", quota_usage_date)
        raise


from schemas.name_schemas import FeedbackSchema
from core.workflow import feedback_names


@router.post("/feedback", response_model=NameSchemaWithThreadOut)
async def feedback(data: FeedbackSchema, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    quota_usage_date = await reserve_quota(session, user.id, "NAMING")
    try:
        result = await feedback_names(data, user.id)
        return NameSchemaWithThreadOut(thread_id=result["thread_id"], names=result["names"]["names"])
    except Exception:
        await refund_quota(session, user.id, "NAMING", quota_usage_date)
        raise
