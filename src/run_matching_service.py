"""
Точка входа для запуска фонового сервиса DriverMatchingService.
"""
import asyncio
import signal
import platform

from src.core.redis import redis_pool
from src.services.matching_service import DriverMatchingService
import redis.asyncio as aioredis


async def main():
    """
    Инициализирует и запускает сервис, обрабатывает корректное завершение.
    """
    redis_client = aioredis.Redis(connection_pool=redis_pool)
    service = DriverMatchingService(redis=redis_client)

    # Создаем задачу для запуска сервиса, чтобы мы могли ее отменить
    service_task = asyncio.create_task(service.run())

    # Проверяем ОС перед добавлением обработчиков сигналов
    if platform.system() != "Windows":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: service_task.cancel())
    
    # Ожидаем завершения задачи.
    try:
        await service_task
    except asyncio.CancelledError:
        print("Service task was cancelled.")
    finally:
        await redis_pool.disconnect()
        print("Matching service stopped and Redis pool disconnected.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПроцесс прерван пользователем (KeyboardInterrupt).")