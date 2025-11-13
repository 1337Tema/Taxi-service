"""
Сервис для поиска и назначения водителей на заказы.
Работает как асинхронный фоновый процесс (consumer).
"""

import asyncio
import logging
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

                # TODO: Шаг 8 - Реализовать логику поиска водителя
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