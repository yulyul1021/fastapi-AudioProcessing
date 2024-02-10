from typing import Annotated
from pydantic import BaseModel, EmailStr, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from fastapi import Form


class UserCreateForm(BaseModel):
    username: str
    password1: str
    password2: str
    email: EmailStr

    @field_validator("username", "password1", "password2", "email")
    def check_empty(cls, v):
        if not v or v.isspace():
            raise ValueError('빈 값은 허용되지 않습니다.')
        return v

    @field_validator("password2")
    def password_match(cls, v, info: FieldValidationInfo):
        if 'password1' in info.data and v != info.data['password1']:
            raise ValueError('비밀번호가 일치하지 않습니다')
        return v

    @classmethod
    def as_form(
        cls,
        username: Annotated[str, Form()],
        password1: Annotated[str, Form()],
        password2: Annotated[str, Form()],
        email: Annotated[EmailStr, Form()]
    ):
        return cls(username=username, password1=password1, password2=password2, email=email)


    class Token(BaseModel):
        access_token: str
        token_type: str