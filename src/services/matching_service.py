"""
Сервис для поиска и назначения водителей на заказы.
Работает как асинхронный фоновый процесс (consumer).
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from redis.asyncio import Redis
import json
import time

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
    NOTIFICATION_CHANNEL = "driver_notifications" # Имя канала для отправки уведомлений
    TIMEOUT_ZSET_KEY = "proposal_timeouts" # Ключ для отложенной очереди таймаутов
    RETRY_STREAM_KEY = "retry_search_events" # Имя стрима для повторного поиска


    def __init__(self, redis: Redis):
        self.redis = redis
        self._running = False
        self.MAX_SEARCH_RADIUS = 20 # Максимальный радиус поиска водителя
        self.DRIVER_LOCK_TIMEOUT = 30 # Время блокировки водителя в секундах
        self.PROPOSAL_TIMEOUT = 25 # Время ожидания ответа водителя на предложение в секундах


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
                    pipe = self.redis.pipeline()
                    for key in set(keys_to_check):
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
    

    async def _timeout_checker(self):
        """
        Фоновый воркер, который проверяет ZSET на наличие истекших предложений.
        """
        logger.info("Воркер проверки таймаутов запущен.")
        while self._running:
            try:
                # Находим все предложения, у которых истек срок
                expired_proposals = await self.redis.zrangebyscore(
                    self.TIMEOUT_ZSET_KEY, 0, time.time()
                )

                if not expired_proposals:
                    await asyncio.sleep(1)  # Пауза, если нет работы
                    continue
                
                logger.info(f"Обнаружены истекшие предложения: {expired_proposals}")

                # Удаляем их из очереди, чтобы не обрабатывать повторно
                await self.redis.zrem(self.TIMEOUT_ZSET_KEY, *expired_proposals)

                for proposal in expired_proposals:
                    ride_id, driver_id_str = proposal.split(":")
                    driver_id = int(driver_id_str)

                    # Снимаем блокировку, только если она все еще принадлежит этому заказу
                    lock_key = f"driver_lock:{driver_id}"
                    current_lock_ride_id = await self.redis.get(lock_key)

                    if current_lock_ride_id == ride_id:
                        logger.warning(f"Таймаут для водителя {driver_id} по заказу {ride_id}. Снимаем блокировку.")
                        await self.redis.delete(lock_key)
                        
                        # Публикуем событие для повторного поиска
                        await self.redis.xadd(
                            self.RETRY_STREAM_KEY,
                            {"ride_id": ride_id, "exclude_driver_id": driver_id}
                        )
                    else:
                        logger.info(f"Таймаут для заказа {ride_id} проигнорирован, т.к. водитель {driver_id} уже не заблокирован этим заказом.")
            
            except Exception as e:
                logger.error(f"Ошибка в воркере проверки таймаутов: {e}", exc_info=True)
                await asyncio.sleep(5)


    async def _order_events_listener(self):
        """
        Основной воркер, который слушает новые заказы и запускает поиск.
        """
        await self._ensure_consumer_group()
        logger.info("Слушатель новых заказов запущен...")
        self._running = True

        while self._running:
            try:
                try:
                    response = await self.redis.xreadgroup(
                        groupname=self.CONSUMER_GROUP,
                        consumername="consumer-1",
                        streams={self.STREAM_KEY: ">"},
                        count=1,
                        block=0,
                    )
                except Exception as e:
                    if "NOGROUP" in str(e):
                        logger.warning("Группа потребителей не найдена (был flushdb?). Пересоздаем...")
                        await self._ensure_consumer_group()
                        continue
                    # Если другая ошибка — пробрасываем дальше
                    raise e

                if not response:
                    continue

                stream_key, messages = response[0]
                message_id, raw_data = messages[0]

                logger.info(f"Получен новый заказ {raw_data} с ID {message_id}")

                try:
                    raw_payload = raw_data['data']
                    
                    if isinstance(raw_payload, str):
                        data = json.loads(raw_payload)
                    elif isinstance(raw_payload, dict):
                        data = raw_payload
                    else:
                        logger.error(f"Unknown data type: {type(raw_payload)}")
                        await self.redis.xack(self.STREAM_KEY, self.CONSUMER_GROUP, message_id)
                        continue

                    # Проверка типа события
                    event_type = raw_data.get('event', data.get('event'))
                    
                    if event_type != 'OrderCreated':
                        await self.redis.xack(self.STREAM_KEY, self.CONSUMER_GROUP, message_id)
                        continue
                    # Валидируем, что данные о координатах пришли
                    start_x = int(data['start_x'])
                    start_y = int(data['start_y'])
                    ride_id = data['ride_id']
                    end_x = int(data.get('end_x', 0))
                    end_y = int(data.get('end_y', 0))
                    price = data.get('price', 0)
                    
                except (KeyError, ValueError) as e:
                    logger.error(f"Некорректные данные в сообщении о заказе {message_id}: {e}")
                    await self.redis.xack(self.STREAM_KEY, self.CONSUMER_GROUP, message_id)
                    continue

                driver_id = await self._find_and_lock_nearest_driver(start_x, start_y, ride_id)

                if driver_id:
                    logger.info(f"Найден и заблокирован водитель: ID {driver_id} для заказа {ride_id}")

                    notification_payload = {
                        "type": "NEW_ORDER_PROPOSAL",
                        "recipient_user_id": driver_id,
                        "data": {
                            "ride_id": ride_id,
                            "start_x": start_x,
                            "start_y": start_y,
                            "end_x": int(data['end_x']), 
                            "end_y": int(data['end_y']),
                            "price": data.get('price', 0)
                        }
                    }

                    await self.redis.publish(
                        self.NOTIFICATION_CHANNEL,
                        json.dumps(notification_payload)
                    )
                    
                    proposal_member = f"{ride_id}:{driver_id}"
                    timeout_score = int(time.time() + self.PROPOSAL_TIMEOUT)
                    await self.redis.zadd(self.TIMEOUT_ZSET_KEY, {proposal_member: timeout_score})
                    
                    await self.redis.xack(self.STREAM_KEY, self.CONSUMER_GROUP, message_id)
                    logger.info(f"Заказ {ride_id} успешно обработан и подтвержден.")

                else:
                    logger.warning(f"Не удалось найти водителя для заказа {data.get('ride_id')}. Заказ остается в очереди.")
                    await asyncio.sleep(1)
                    continue

            except asyncio.CancelledError:
                logger.info("Цикл обработки остановлен.")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле обработки DriverMatchingService: {e}", exc_info=True)
                await asyncio.sleep(5)


    async def run(self):
        """
        Основной цикл работы сервиса.
        Слушает новые сообщения в потоке и обрабатывает их.
        """
        self._running = True
        
        # Запускаем оба воркера параллельно
        listener_task = asyncio.create_task(self._order_events_listener())
        timeout_task = asyncio.create_task(self._timeout_checker())
        
        logger.info("DriverMatchingService запущен с двумя воркерами.")
        
        # Ожидаем завершения любой из задач (в случае ошибки)
        done, pending = await asyncio.wait(
            [listener_task, timeout_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Если одна задача завершилась, отменяем другую для чистого выхода
        for task in pending:
            task.cancel()
        
        logger.info("DriverMatchingService остановлен.")

    def stop(self):
        """Останавливает основной цикл работы."""
        self._running = False
        logger.info("Получен сигнал на остановку DriverMatchingService.")