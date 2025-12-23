"""
Эндпоинты аутентификации: регистрация и логин.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.user import UserCreateSchema, UserLoginSchema, TokenSchema
from src.services.user_service import register_user, authenticate_user, create_access_token
from src.core.db import get_async_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenSchema, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreateSchema,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Регистрирует нового пользователя и возвращает JWT access_token.
    """
    user = await register_user(user_data, db)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenSchema)
async def login(
    user_data: UserLoginSchema,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Логин пользователя. Проверяет email и пароль.
    Возвращает JWT access_token.
    """
    user = await authenticate_user(user_data, db)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
