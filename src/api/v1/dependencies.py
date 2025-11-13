"""Модуль с общими зависимостями для API."""

from typing import Optional
from fastapi import HTTPException, status, Query, WebSocket


async def get_current_user_id_stub(
    # Добавляем возможность получать токен из query-параметра для WebSocket
    token: Optional[str] = Query(None, description="Токен аутентификации для WebSocket")
) -> int:
    """
    Временная функция-заглушка для получения ID текущего пользователя.
    В будущем будет заменена на полноценную JWT-аутентификацию.
    Для WebSocket токен передается как query-параметр.
    """
    # Для целей тестирования просто возвращаем ID.
    # В реальном приложении здесь будет логика валидации токена.
    return 1