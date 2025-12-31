"""Главный файл приложения FastAPI."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uuid
import logging
from contextvars import ContextVar
import redis.asyncio as aioredis

# Импорты ядра и настроек
from src.core.redis import redis_pool
from src.services.notification_service import notification_manager
from src.core.logging_config import setup_logging, RequestIdFilter
from src.core.db import engine, Base

# Импортируем модели, чтобы SQLAlchemy увидела их и создала таблицы
from src.models.user import User
from src.models.driver import Driver
from src.models.passenger import Passenger
from src.models.ride import Ride

# Импортируем роутеры
from src.api.v1 import drivers as drivers_v1
from src.api.v1 import notifications as notifications_v1
from src.api.v1 import auth as auth_v1
from src.api.v1 import rides as rides_v1

# ContextVar для хранения request_id в рамках одного запроса
request_id_var = ContextVar("request_id", default="N/A")

# Настраиваем логирование при старте
setup_logging()
logger = logging.getLogger("src.main")


async def redis_pubsub_listener():
    """Слушает канал Redis и отправляет уведомления через WebSocket."""
    redis_client = aioredis.Redis(connection_pool=redis_pool)
    pubsub = redis_client.pubsub()

    driver_channel = "driver_notifications"
    passenger_channel = "passenger_notifications"

    await pubsub.subscribe(driver_channel, passenger_channel)
    logger.info(f"Подписка на Redis каналы '{driver_channel}', '{passenger_channel}' установлена.")

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
            if message and message["type"] == "message":
                try:
                    payload = json.loads(message["data"])
                    recipient_id = int(payload.get("recipient_user_id"))
                    message_to_send = {
                        "type": payload.get("type"),
                        "data": payload.get("data")
                    }
                    await notification_manager.send_personal_message(
                        recipient_id, message_to_send
                    )
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.error(f"Не удалось обработать сообщение из Pub/Sub: {e}")

            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        logger.info("Слушатель Pub/Sub остановлен.")
    finally:
        await pubsub.close()
        logger.info("Подписка на Redis Pub/Sub закрыта.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Жизненный цикл:
    1. Создаем таблицы в БД (вместо Alembic).
    2. Запускаем слушателя Redis.
    """
    logger.info("Application startup...")


    async with engine.begin() as conn:
        # Эта команда создаст все таблицы, если их нет
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")

    listener_task = asyncio.create_task(redis_pubsub_listener())

    yield

    logger.info("Application shutdown...")
    listener_task.cancel()
    await listener_task
    await redis_pool.disconnect()
    logger.info("Redis pool disconnected.")


app = FastAPI(
    title="Taxi Grid Service",
    description="Сервис для заказа такси в сеточном городе N×M",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    fastapi_logger = logging.getLogger("fastapi")
    filter = RequestIdFilter(request_id_storage=request_id_var)
    fastapi_logger.addFilter(filter)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    fastapi_logger.removeFilter(filter)
    return response


app.include_router(drivers_v1.router, prefix="/api/v1")
app.include_router(notifications_v1.router, prefix="/api/v1")
app.include_router(auth_v1.router, prefix="/api/v1", tags=["Auth"])
app.include_router(rides_v1.router, prefix="/api/v1", tags=["Rides"])


@app.get("/healthcheck", tags=["Healthcheck"])
async def healthcheck():
    return {"status": "ok"}