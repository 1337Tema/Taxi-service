"""Модуль с общими зависимостями для API."""

from typing import Optional
from fastapi import HTTPException, status, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from src.core.config import settings
from src.core.db import get_async_session
from src.models.user import User

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> int:
    """
    Извлекает и валидирует JWT токен, возвращает ID текущего пользователя.
    """
    try:
        # Декодируем JWT токен
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем, что пользователь существует в базе данных
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return int(user_id)


async def get_current_user_id_websocket(
    token: Optional[str] = Query(None, description="Токен аутентификации для WebSocket"),
    db: AsyncSession = Depends(get_async_session)
) -> int:
    """
    Валидация JWT токена для WebSocket соединений.
    Токен передается как query-параметр.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не предоставлен"
        )
    
    try:
        # Декодируем JWT токен
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
    
    # Проверяем, что пользователь существует в базе данных
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    return int(user_id)


# Для обратной совместимости с существующим кодом
async def get_current_user_id_stub(
    token: Optional[str] = Query(None, description="Токен аутентификации для WebSocket")
) -> int:
    """
    DEPRECATED: Используйте get_current_user_id или get_current_user_id_websocket
    Временная заглушка для тестирования без токенов.
    """
    return 1