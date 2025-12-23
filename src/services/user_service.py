"""
Сервис для управления пользователями: регистрация, аутентификация и JWT.
"""

from typing import Optional
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
import jwt

from src.models.user import User
from src.schemas.user import UserCreateSchema, UserLoginSchema
from src.core.config import settings

# Настройка хеширования паролей bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def register_user(user_data: UserCreateSchema, db: AsyncSession) -> User:
    """
    Регистрирует нового пользователя.
    
    Проверяет уникальность email, хеширует пароль и сохраняет пользователя в БД.
    """
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user: Optional[User] = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def authenticate_user(
    user_data: UserLoginSchema, db: AsyncSession
) -> User:
    """
    Проверяет email и пароль пользователя.
    Если аутентификация успешна — возвращает объект User.
    Если нет — HTTP 401 Unauthorized.
    """
    result = await db.execute(select(User).where(User.email == user_data.email))
    user: Optional[User] = result.scalar_one_or_none()
    if not user or not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def create_access_token(user_id: int) -> str:
    """
    Генерирует JWT access_token для пользователя.
    Payload: {"sub": user_id, "exp": <expire>}
    Срок действия берется из настроек.
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token
