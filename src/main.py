"""Главный файл приложения FastAPI."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio
import json
from fastapi import FastAPI
import logging

# Импортируем роутеры и сервисы
from src.api.v1 import drivers as drivers_v1
from src.api.v1 import notifications as notifications_v1
from src.core.redis import redis_pool
from src.services.notification_service import notification_manager
import redis.asyncio as aioredis 

# Настройка базовой конфигурации логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def redis_pubsub_listener():
    """Слушает канал Redis и отправляет уведомления через WebSocket."""
    # Создаем отдельное подключение для Pub/Sub
    redis_client = aioredis.Redis(connection_pool=redis_pool)
    pubsub = redis_client.pubsub()
    
    # Имена каналов
    driver_channel = "driver_notifications"
    passenger_channel = "passenger_notifications"
    
    # Подписываемся сразу на несколько каналов
    await pubsub.subscribe(driver_channel, passenger_channel)
    
    logger.info(f"Подписка на Redis каналы '{driver_channel}', '{passenger_channel}' установлена.")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
            if message and message["type"] == "message":
                channel = message['channel'] # НОВОЕ: Определяем, из какого канала пришло сообщение
                logger.info(f"Получено сообщение из канала '{channel}': {message['data']}")
                
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
    Контекстный менеджер для управления жизненным циклом приложения.
    Выполняется при старте и остановке приложения.
    """
    logger.info("Application startup...")
    
    # Запускаем слушателя Pub/Sub как фоновую задачу
    listener_task = asyncio.create_task(redis_pubsub_listener())
    
    yield
    
    # При остановке приложения отменяем задачу
    logger.info("Application shutdown...")
    listener_task.cancel()
    # Ожидаем завершения задачи
    await listener_task
    
    await redis_pool.disconnect()
    logger.info("Redis pool disconnected.")


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