"""Модуль для управления асинхронным клиентом и пулом соединений Redis."""

from typing import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis

from .config import settings

# Создаем асинхронный пул соединений к Redis.
redis_pool = aioredis.ConnectionPool.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    decode_responses=True,
)


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    Функция-зависимость для FastAPI для получения клиента Redis из пула соединений.

    Обеспечивает, что клиент будет корректно закрыт после использования.
    """
    async with aioredis.Redis(connection_pool=redis_pool) as client:
        yield client