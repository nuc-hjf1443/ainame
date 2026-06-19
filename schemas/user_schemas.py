from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator, ValidationError

RawPasswordStr = Annotated[str, Field(..., min_length=3, max_length=50)]
RawUserNameStr = Annotated[str, Field(..., min_length=3, max_length=50)]

class RegisterIn(BaseModel):
    email: EmailStr
    username: RawPasswordStr
    password: RawPasswordStr
    confirm_password: RawPasswordStr
    # 验证用户的有效性
    code: Annotated[str, Field(..., min_length=4, max_length=4)]

    # 完成确认密码的校验
    @model_validator(mode="after")
    def password_is_valid(self, password:str):
        password = self.password
        confirm_password = self.confirm_password
        if password != confirm_password:
            raise ValidationError("Passwords don't match")
        return self


# 存入数据库的少数字段
class UserCreateSchema(BaseModel):
    email: EmailStr
    username: RawUserNameStr
    password: RawUserNameStr


class LoginIn(BaseModel):
    email:EmailStr
    password:RawPasswordStr


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:Annotated[int,Field(...)]
    username:RawUserNameStr
    email:EmailStr
    role: str = "C_END"
    is_banned: bool = False


class LoginOut(BaseModel):
    user:UserSchema
    token:str
