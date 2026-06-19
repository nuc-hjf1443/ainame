import random
import string
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi_mail import MessageSchema, MessageType, FastMail
from pydantic import EmailStr
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio.session import AsyncSession

from dependencies import get_email, get_session
from models.user import User
from repository.user_repo import EmailCodeRepository, UserRepository
from core.redisconfig import get_redis_client

router = APIRouter(prefix="/auth", tags=["auth"])

# 发送验证码给用户

@router.get("/code")
async def get_email_code(email: Annotated[EmailStr, Query(...)],
                         fastmail:FastMail=Depends(get_email),
                         session:AsyncSession=Depends(get_session),
                         redis: Redis = Depends(get_redis_client)):
    # 1. 生成验证码
    source = string.digits * 4
    # 从source这个字符串随机取4位数
    code = "".join(random.sample(source, 4))
    # 2. 创建一个邮件, 系统把邮件发给谁
    message = MessageSchema(
        subject="[ai起名字app]注册验证码",
        recipients=[email],
        body=f"您的验证码是:{code},五分钟有效，请及时注册账号",
        subtype=MessageType.plain
    )
    # 3. 发送邮件
    await fastmail.send_message(message)
    # 4. 把发送的邮件信息保存起来
    # email_repository = EmailCodeRepository(session=session)
    # await email_repository.create_email_code(email, code)
    await redis.set(email, code, ex=300)

    return {"message": "验证码发送成功"}


from schemas.user_schemas import RegisterIn, UserCreateSchema, LoginIn


# 功能：用户注册。向用户表插入一条数据
# 后台要接收用户的信息。设计对象来接收，把接收对象转成数据库对象，存入数据库
@router.post("/register")
async def register(userinfo: RegisterIn, session: AsyncSession=Depends(get_session),
                   redis: Redis = Depends(get_redis_client)):
    # 向用户表中插入数据
    userRepository = UserRepository(session=session)
    # 1. 邮箱是否被注册
    email_exist = await userRepository.email_is_exist(userinfo.email)
    if email_exist:
        raise HTTPException(status_code=400, detail="该邮箱已经注册，请直接登录")
    # 2. 验证码是否正确，如果不对就不允许注册
    # emailCodeRepository = EmailCodeRepository(session=session)
    # email_code_bool = await emailCodeRepository.check_email_code(userinfo.email, userinfo.code)
    # key是email
    email_code= await redis.get(userinfo.email)
    if (not email_code) or (userinfo.code != email_code):
        raise HTTPException(400, detail="验证码错误或者已经过期")

    # 3. 允许注册
    userCreateSchema = UserCreateSchema(email=userinfo.email, username=userinfo.username, password=userinfo.password)
    await userRepository.create_user(userCreateSchema)
    await redis.delete(userinfo.email)
    return {"message": "恭喜您注册成功"}


from core.auth import AuthHandler
from schemas.user_schemas import LoginOut
authHandler = AuthHandler()
@router.post("/login", response_model=LoginOut)
async def login(userinfo:LoginIn, session:AsyncSession=Depends(get_session)):
    # 获取信息，邮箱，根据邮箱才能知道你是不是我们的会员
    # 1. 确定是已经注册用户
    userRepository = UserRepository(session=session)
    user:User|None = await userRepository.get_user_by_email(userinfo.email)
    if not user:
        raise HTTPException(status_code=400, detail="该用户不存在！")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="账号已被封禁，请联系管理员")
    # 2. 看密码是否正确
    if not user.check_password(userinfo.password):
        raise HTTPException(status_code=400, detail="密码输入错误，请核对后输入！")
    # 3. 密码正确允许登陆,登录的方法是，给用户返回一个令牌。用户拿着这个令牌，下次来证明已经登录
    tokens = authHandler.encode_login_token(user.id)
    return {
        "user": user,
        "token": tokens['access_token']
    }
