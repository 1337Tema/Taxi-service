"""
Сервис для поиска и назначения водителей на заказы.
Работает как асинхронный фоновый процесс (consumer).
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from redis.asyncio import Redis

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DriverMatchingService:
    """
    Слушает поток 'order_events', ищет водителя для новых заказов
    и инициирует процесс назначения.
    """
    STREAM_KEY = "order_events"  # Ключ потока для событий заказов
    CONSUMER_GROUP = "matching_group"  # Имя группы потребителей

    def __init__(self, redis: Redis):
        self.redis = redis
        self._running = False
        self.MAX_SEARCH_RADIUS = 20 # Максимальный радиус поиска водителя
        self.DRIVER_LOCK_TIMEOUT = 30 # Время блокировки водителя в секундах

    async def _ensure_consumer_group(self):
        """
        Убеждается, что группа потребителей существует.
        Если стрима или группы нет, они будут созданы.
        """
        try:
            await self.redis.xgroup_create(
                name=self.STREAM_KEY,
                groupname=self.CONSUMER_GROUP,
                id="0",  # Начинаем читать с самого начала
                mkstream=True,  # Создать стрим, если его нет
            )
            logger.info(f"Создана группа потребителей '{self.CONSUMER_GROUP}' для потока '{self.STREAM_KEY}'.")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Группа потребителей '{self.CONSUMER_GROUP}' уже существует.")
            else:
                logger.error(f"Не удалось создать группу потребителей: {e}")
                raise


    async def _lock_driver(self, driver_id: int, ride_id: str) -> bool:
        """
        Атомарно пытается установить блокировку на водителя.

        Args:
            driver_id: ID водителя, которого нужно заблокировать.
            ride_id: ID заказа, который инициирует блокировку.

        Returns:
            True, если блокировка установлена успешно, иначе False.
        """
        lock_key = f"driver_lock:{driver_id}"
        # `set` с параметром `nx=True` вернет True только если ключ был установлен.
        # `ex` устанавливает время жизни ключа.
        was_set = await self.redis.set(
            lock_key, ride_id, ex=self.DRIVER_LOCK_TIMEOUT, nx=True
        )
        return was_set

    async def _find_and_lock_nearest_driver(
        self, start_x: int, start_y: int, ride_id: str
    ) -> Optional[int]:
        """
        Ищет ближайшего СВОБОДНОГО (не заблокированного) водителя и блокирует его.

        Returns:
            ID заблокированного водителя или None.
        """
        logger.info(f"Начинаем поиск и блокировку водителя из точки ({start_x}, {start_y}) для заказа {ride_id}")

        # Проверяем водителей в точке заказа (радиус 0)
        cell_key = f"cell:{start_x}:{start_y}"
        drivers_in_cell = await self.redis.hkeys(cell_key)
        if drivers_in_cell:
            candidate_ids = sorted([int(d) for d in drivers_in_cell])
            logger.info(f"Найдены кандидаты в ячейке 0: {candidate_ids}")
            # Пытаемся заблокировать каждого кандидата по очереди
            for driver_id in candidate_ids:
                if await self._lock_driver(driver_id, ride_id):
                    logger.info(f"Водитель {driver_id} успешно заблокирован.")
                    return driver_id

        # Расширяем поиск по спирали
        for radius in range(1, self.MAX_SEARCH_RADIUS + 1):
            candidate_ids = []
            # Итерируемся по периметру квадрата с текущим радиусом
            for i in range(-radius, radius + 1):
                # Горизонтальные стороны
                keys_to_check = [
                    f"cell:{start_x + i}:{start_y + radius}",
                    f"cell:{start_x + i}:{start_y - radius}"
                ]
                # Вертикальные стороны (исключая углы, чтобы не проверять дважды)
                if abs(i) != radius:
                     keys_to_check.extend([
                         f"cell:{start_x + radius}:{start_y + i}",
                         f"cell:{start_x - radius}:{start_y + i}"
                     ])
                
                # За один запрос получаем водителей из всех ячеек на периметре
                if keys_to_check:
                    # Используем SUNION для объединения множеств ключей, но HKEYS возвращает списки
                    # Поэтому делаем несколько запросов в pipeline
                    pipe = self.redis.pipeline()
                    for key in set(keys_to_check): # set() для уникальности
                        pipe.hkeys(key)
                    
                    results = await pipe.execute()
                    
                    for driver_list in results:
                        candidate_ids.extend([int(d) for d in driver_list])

            if candidate_ids:
                sorted_candidates = sorted(candidate_ids)
                logger.info(f"Найдены кандидаты в радиусе {radius}: {sorted_candidates}")
                # Пытаемся заблокировать каждого кандидата
                for driver_id in sorted_candidates:
                    if await self._lock_driver(driver_id, ride_id):
                        logger.info(f"Водитель {driver_id} успешно заблокирован.")
                        return driver_id

        logger.warning(f"Свободные водители не найдены в радиусе {self.MAX_SEARCH_RADIUS} от ({start_x}, {start_y})")
        return None

    async def run(self):
        """
        Основной цикл работы сервиса.
        Слушает новые сообщения в потоке и обрабатывает их.
        """
        await self._ensure_consumer_group()
        logger.info("DriverMatchingService запущен и ожидает новые заказы...")
        self._running = True

        while self._running:
            try:
                response = await self.redis.xreadgroup(
                    groupname=self.CONSUMER_GROUP,
                    consumername="consumer-1",
                    streams={self.STREAM_KEY: ">"},
                    count=1,
                    block=0,
                )

                if not response:
                    continue

                stream_key, messages = response[0]
                message_id, data = messages[0]

                logger.info(f"Получен новый заказ {data} с ID {message_id}")

                try:
                    # Валидируем, что данные о координатах пришли
                    start_x = int(data['start_x'])
                    start_y = int(data['start_y'])
                    ride_id = data['ride_id']
                except (KeyError, ValueError) as e:
                    logger.error(f"Некорректные данные в сообщении о заказе {message_id}: {e}")
                    # Подтверждаем "битое" сообщение, чтобы оно не блокировало очередь
                    await self.redis.xack(self.STREAM_KEY, self.CONSUMER_GROUP, message_id)
                    continue

                driver_id = await self._find_and_lock_nearest_driver(start_x, start_y, ride_id)

                if driver_id:
                    logger.info(f"Найден и заблокирован водитель: ID {driver_id} для заказа {ride_id}")
                    # TODO: Шаг 9 - Реализовать логику блокировки водителя
                else:
                    logger.warning(f"Не удалось найти водителя для заказа {data.get('ride_id')}. Заказ остается в очереди.")
                    # TODO: Реализовать логику постановки в очередь ожидания
                    # Пока просто оставляем сообщение необработанным (не делаем xack)
                    # Оно будет передоставлено другому консьюмеру через некоторое время
                    await asyncio.sleep(10) # Ждем перед следующей попыткой
                    continue

                # TODO: Шаг 9 - Реализовать логику блокировки

                await self.redis.xack(self.STREAM_KEY, self.CONSUMER_GROUP, message_id)
                logger.info(f"Заказ {data.get('ride_id')} успешно обработан и подтвержден.")

            except asyncio.CancelledError:
                # Это исключение возникает, когда задача отменяется (например, при остановке)
                logger.info("Цикл обработки остановлен.")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле обработки DriverMatchingService: {e}", exc_info=True)
                await asyncio.sleep(5)

    def stop(self):
        """Останавливает основной цикл работы."""
        self._running = False
        # Для немедленной остановки можно отменить текущую задачу ожидания redis
        # Но простой установки флага обычно достаточно для корректного завершения
        logger.info("Получен сигнал на остановку DriverMatchingService.")