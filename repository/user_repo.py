from datetime import datetime
from datetime import timedelta

from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.user import EmailCode, User
from schemas.user_schemas import UserCreateSchema


# 与email交互的对象
class EmailCodeRepository():

    def __init__(self, session:AsyncSession):
        self.session = session

    async def create_email_code(self, email:str, code:str):
        """
        把一条emailcode数据插入到数据库
        :param email:
        :param code:
        :return:
        """
        async with self.session.begin():
            email_code = EmailCode(email=email, code=code)
            self.session.add(email_code)

            return email_code

    async def check_email_code(self, email:str, code:str):
        """
        校验验证码
        :param email:
        :param code:
        :return:
        """
        async with self.session.begin():
            email_code = await self.session.scalar(select(EmailCode)
                                                   .filter(EmailCode.email==email, EmailCode.code==code))

            if not email_code:
                return False
            if(datetime.now() - email_code.created_time) >= timedelta(minutes=5):
                return False
            return True


# 与user表交互的对象
class UserRepository():
    def __init__(self, session:AsyncSession):
        self.session = session

    async def get_user_by_email(self, email:str):
        async with self.session.begin():
            result = await self.session.execute(select(User).where(User.email==email))
            return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int):
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user:UserCreateSchema):
        async with self.session.begin():
            user = User(**user.model_dump())
            self.session.add(user)
            return user

    async def email_is_exist(self, email:str):
        async with self.session.begin():
            stmt = select(exists().where(User.email==email))
            return await self.session.scalar(stmt)
