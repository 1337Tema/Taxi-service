"""
Pydantic-схемы для пользователя и аутентификации.
"""

from pydantic import BaseModel, EmailStr, Field


class UserCreateSchema(BaseModel):
    """Схема для регистрации нового пользователя."""
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=6, description="Пароль пользователя")


class UserLoginSchema(BaseModel):
    """Схема для логина пользователя."""
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., description="Пароль пользователя")


class UserReadSchema(BaseModel):
    """Схема для ответа с данными пользователя."""
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    """Схема для JWT токена."""
    access_token: str
    token_type: str = "bearer"
