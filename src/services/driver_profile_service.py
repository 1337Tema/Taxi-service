"""Сервис для управления профилем и состоянием водителя."""

import logging
from typing import Optional
from redis.asyncio import Redis

from src.schemas.driver import DriverPresenceSchema, DriverStatus

# Настройка логирования
logger = logging.getLogger(__name__)


class DriverProfileService:
    """
    Инкапсулирует бизнес-логику, связанную с состоянием водителя.
    - Обновление статуса (online/offline)
    - Обновление местоположения в геоиндексе Redis
    """
    def __init__(self, redis: Redis):
        self.redis = redis


    async def _get_driver_previous_location(self, driver_id: int) -> Optional[tuple[int, int]]:
        """Вспомогательный метод для получения предыдущей локации водителя из Redis."""
        location_str = await self.redis.get(f"driver_location:{driver_id}")
        if location_str:
            try:
                x_str, y_str = location_str.split(":")
                return int(x_str), int(y_str)
            except (ValueError, TypeError):
                logger.warning(
                    f"Некорректный формат локации для водителя {driver_id} в Redis: {location_str}"
                )
        return None


    async def update_presence(self, driver_id: int, presence_data: DriverPresenceSchema) -> None:
        """
        Обновляет статус и местоположение водителя в Redis.

        Алгоритм:
        1. Получить предыдущую локацию водителя, чтобы очистить старую ячейку геоиндекса.
        2. Если водитель был где-то на карте, удалить его ID из старой ячейки `cell:X:Y`.
        3. Если новый статус - 'online', добавить водителя в новую ячейку геоиндекса `cell:X:Y`.
        4. Сохранить новую локацию водителя в `driver_location:{driver_id}` для будущих обновлений.
        5. Если новый статус - 'offline', удалить информацию о его локации.
        """
        logger.info(f"Обновление присутствия для водителя {driver_id}: статус {presence_data.status.value}")

        # Шаг 1: Получаем предыдущую локацию
        previous_location = await self._get_driver_previous_location(driver_id)

        # Используем Redis Pipeline для атомарного выполнения нескольких команд
        async with self.redis.pipeline() as pipe:
            # Шаг 2: Если водитель был на карте, удаляем его из старой ячейки
            if previous_location:
                prev_x, prev_y = previous_location
                old_cell_key = f"cell:{prev_x}:{prev_y}"
                pipe.hdel(old_cell_key, str(driver_id))
                logger.debug(f"Водитель {driver_id} удален из старой ячейки {old_cell_key}")

            # Шаги 3-5: Обрабатываем новый статус
            new_location = presence_data.location
            new_location_key = f"driver_location:{driver_id}"
            new_location_str = f"{new_location.x}:{new_location.y}"

            if presence_data.status == DriverStatus.ONLINE:
                # Добавляем в новую ячейку и обновляем текущую позицию
                new_cell_key = f"cell:{new_location.x}:{new_location.y}"
                pipe.hset(new_cell_key, str(driver_id), presence_data.status.value)
                pipe.set(new_location_key, new_location_str)
                logger.debug(f"Водитель {driver_id} добавлен в ячейку {new_cell_key} и его локация обновлена")
            else: # offline или busy
                # Просто удаляем ключ с его локацией
                pipe.delete(new_location_key)
                logger.debug(f"Локация водителя {driver_id} удалена (статус offline/busy)")

            # Выполняем все команды в транзакции
            await pipe.execute()

        logger.info(f"Присутствие для водителя {driver_id} успешно обновлено в Redis.")