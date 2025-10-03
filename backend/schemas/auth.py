from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(
        ...,
        title="Имя пользователя",
        description="Уникальное имя пользователя",
        examples=["ivan_petrov"],
    )
    email: EmailStr = Field(
        ...,
        title="Электронная почта",
        description="Email пользователя",
        examples=["ivan@example.com"],
    )
    password: str = Field(
        ...,
        title="Пароль",
        description="Пароль пользователя",
        examples=["strongpassword123"],
    )


class RegisterResponse(BaseModel):
    user_uuid: UUID = Field(
        ...,
        title="UUID пользователя",
        description="Уникальный идентификатор пользователя",
    )
    username: str = Field(
        ...,
        title="Имя пользователя",
        description="Зарегистрированное имя пользователя",
    )
    email: str = Field(
        ...,
        title="Электронная почта",
        description="Зарегистрированный email",
    )
    created_at: datetime | None = Field(
        None,
        title="Дата создания",
        description="Время создания пользователя",
    )
    updated_at: datetime | None = Field(
        None,
        title="Дата обновления",
        description="Время последнего обновления",
    )


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        title="Имя пользователя",
        description="Зарегистрированное имя пользователя",
        examples=["ivan_petrov"],
    )
    password: str = Field(
        ...,
        title="Пароль",
        description="Пароль пользователя",
        examples=["strongpassword123"],
    )


class LoginResponse(BaseModel):
    token: str = Field(
        ...,
        title="JWT токен",
        description="Токен аутентификации после входа в систему",
    )
