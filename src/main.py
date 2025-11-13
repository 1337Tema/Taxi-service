"""Главный файл приложения FastAPI."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
import logging

# Импортируем роутеры
from src.api.v1 import drivers as drivers_v1
from src.api.v1 import notifications as notifications_v1
from src.core.redis import redis_pool

# Настройка базовой конфигурации логирования
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    Выполняется при старте и остановке приложения.
    """
    logging.info("Application startup...")
    logging.info("Redis pool created.")
    yield
    await redis_pool.disconnect()
    logging.info("Redis pool disconnected.")
    logging.info("Application shutdown.")


app = FastAPI(
    title="Taxi Grid Service",
    description="Сервис для заказа такси в сеточном городе N×M",
    version="0.1.0",
    lifespan=lifespan,
)

# Подключаем роутеры API
app.include_router(drivers_v1.router, prefix="/api/v1")
app.include_router(notifications_v1.router, prefix="/api/v1")


@app.get("/healthcheck", tags=["Healthcheck"])
async def healthcheck():
    """Проверка доступности сервиса."""
    return {"status": "ok"}