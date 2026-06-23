from core.mailtools import create_mail_instance
from fastapi_mail import FastMail
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_403_FORBIDDEN

import settings


async def get_email() -> FastMail:
    return create_mail_instance()

from models import AsyncSessionFactory

async def get_session():
    session = AsyncSessionFactory()
    try:
        # yield 借出去session，意味着如果用完，再还回来
        yield session
    finally:
        await session.close()


from core.auth import AuthHandler
from models.user import User
from repository.user_repo import UserRepository


auth_handler = AuthHandler()
optional_security = HTTPBearer(auto_error=False)


def get_optional_user_id(
        auth: HTTPAuthorizationCredentials | None = Security(optional_security)
) -> int | None:
    if not auth:
        return None
    return int(auth_handler.decode_access_token(auth.credentials))


async def get_current_user(
        user_id: int = Depends(auth_handler.auth_access_dependency),
        session: AsyncSession = Depends(get_session)
) -> User:
    user_repository = UserRepository(session=session)
    user = await user_repository.get_user_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="用户不存在或无权访问")
    if user.is_deleted:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="账号已注销")
    if user.is_banned:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="账号已被封禁")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="仅管理员可访问")
    return current_user


def require_mock_payment_enabled() -> None:
    if not settings.ENABLE_MOCK_PAYMENT:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="当前环境未启用模拟支付")
