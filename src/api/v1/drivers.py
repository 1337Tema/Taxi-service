"""API эндпоинты для управления состоянием водителя."""

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis

from src.core.redis import get_redis_client
from src.schemas.driver import DriverPresenceSchema
from src.services.driver_profile_service import DriverProfileService
from .dependencies import get_current_user_id

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.put(
    "/me/presence",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Обновление статуса и местоположения водителя (Heartbeat)",
    description="Водитель периодически отправляет этот запрос, чтобы подтвердить свой онлайн-статус и текущие координаты.",
)
async def update_driver_presence(
    presence_data: DriverPresenceSchema,
    driver_id: int = Depends(get_current_user_id),
    redis_client: Redis = Depends(get_redis_client),
):
    """
    Обновляет присутствие водителя в системе.

    - **presence_data**: Тело запроса с новым статусом и локацией.
    - **driver_id**: ID водителя, полученный из токена аутентификации (сейчас - заглушка).
    - **redis_client**: Асинхронный клиент Redis, внедренный через зависимость.
    """
    service = DriverProfileService(redis_client)
    await service.update_presence(driver_id, presence_data)
    # При успешном обновлении возвращаем пустой ответ со статусом 204
    return None