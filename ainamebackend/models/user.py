from datetime import datetime

from sqlalchemy import Boolean, Integer, String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from pwdlib import PasswordHash

from . import Base


password_hash = PasswordHash.recommended()


class User(Base):
    __tablename__ = "user"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email:Mapped[str] = mapped_column(String(100), unique=True)
    username:Mapped[str] = mapped_column(String(100))
    _password:Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="C_END", server_default="C_END")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, server_default=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    # 1. 校验数据，密码是否正确
    # *args可以接收任意不带名字的参数
    # **kwargs 能接收任意多个带名字的参数
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = kwargs.pop("password", None)
        if password:
            # 增加一个变量password
            self.password = password
        if self.role is None:
            self.role = "C_END"
        if self.is_banned is None:
            self.is_banned = False
        if self.is_deleted is None:
            self.is_deleted = False

    @property
    def password(self):
        return self._password

    # 设置password
    @password.setter
    def password(self, password):
        self._password = password_hash.hash(password)

    # 校验密码
    def check_password(self, password):
        return password_hash.verify(password, self._password)


class EmailCode(Base):
    __tablename__ = "email_code"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email:Mapped[str] = mapped_column(String(100))
    code:Mapped[str] = mapped_column(String(100))
    created_time:Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
