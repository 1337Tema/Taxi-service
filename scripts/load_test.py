"""
Простой скрипт для нагрузочного тестирования ключевых компонентов сервиса.
"""
import asyncio
import httpx
import random
import time
import redis.asyncio as aioredis
import json

# --- Настройки ---
BASE_URL = "http://127.0.0.1:8000/api/v1"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

NUM_DRIVERS = 1000  # Количество водителей в системе (согласно ТЗ)
GRID_N = 100
GRID_M = 100

HEARTBEAT_REQUESTS = 2000  # Количество heartbeat-запросов для теста
MATCHING_REQUESTS = 500   # Количество заказов для теста

# --- Вспомогательные функции ---

async def setup_drivers(redis_client):
    """Создает и размещает водителей на карте."""
    print(f"--- Создание {NUM_DRIVERS} водителей... ---")
    pipe = redis_client.pipeline()
    # Очищаем старые данные
    await redis_client.flushdb()
    
    for i in range(1, NUM_DRIVERS + 1):
        x, y = random.randint(0, GRID_N - 1), random.randint(0, GRID_M - 1)
        cell_key = f"cell:{x}:{y}"
        location_key = f"driver_location:{i}"
        pipe.hset(cell_key, str(i), "online")
        pipe.set(location_key, f"{x}:{y}")
    
    await pipe.execute()
    print("Водители успешно созданы и размещены.")

async def run_heartbeat_test():
    """Тестирует эндпоинт обновления присутствия."""
    print(f"\n--- Тест 1: Запуск {HEARTBEAT_REQUESTS} Heartbeat-запросов... ---")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for _ in range(HEARTBEAT_REQUESTS):
            driver_id = random.randint(1, NUM_DRIVERS)
            # Для простоты используем заглушку, которая всегда возвращает ID=1.
            # В реальности, здесь был бы JWT токен конкретного водителя.
            # Но нагрузку на сервис это создает идентичную.
            url = f"{BASE_URL}/drivers/me/presence?token=driver_{driver_id}"
            payload = {
                "status": "online",
                "location": {
                    "x": random.randint(0, GRID_N - 1),
                    "y": random.randint(0, GRID_M - 1),
                }
            }
            tasks.append(client.put(url, json=payload))
        
        start_time = time.monotonic()
        responses = await asyncio.gather(*tasks)
        end_time = time.monotonic()

        total_time = end_time - start_time
        success_count = sum(1 for r in responses if r.status_code == 204)
        
        print(f"Выполнено {HEARTBEAT_REQUESTS} запросов за {total_time:.2f} сек.")
        print(f"Успешных запросов: {success_count} ({success_count / HEARTBEAT_REQUESTS * 100:.1f}%)")
        if success_count > 0:
            print(f"Среднее время на запрос: {total_time / success_count * 1000:.2f} мс")
            print(f"RPS (Requests Per Second): {success_count / total_time:.2f}")

async def run_matching_test(redis_client):
    """Тестирует производительность DriverMatchingService."""
    print(f"\n--- Тест 2: Создание {MATCHING_REQUESTS} заказов для Matching Service... ---")
    
    tasks = []
    for i in range(MATCHING_REQUESTS):
        ride_id = f"test_ride_{i}"
        payload = {
            "ride_id": ride_id,
            "start_x": str(random.randint(0, GRID_N - 1)),
            "start_y": str(random.randint(0, GRID_M - 1)),
        }
        tasks.append(redis_client.xadd("order_events", payload))
        
    start_time = time.monotonic()
    await asyncio.gather(*tasks)
    end_time = time.monotonic()

    total_time = end_time - start_time
    print(f"Добавлено {MATCHING_REQUESTS} заказов в стрим за {total_time:.2f} сек.")
    print("Наблюдайте за логами 'run_matching_service.py' для оценки скорости обработки.")


async def main():
    redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    
    # 1. Подготовка
    await setup_drivers(redis_client)
    
    # 2. Тест Heartbeat API
    await run_heartbeat_test()
    
    # 3. Тест Matching Service
    # Небольшая пауза, чтобы сервис успел обработать heartbeat-ы
    await asyncio.sleep(2)
    await run_matching_test(redis_client)
    
    await redis_client.close()

if __name__ == "__main__":
    # Убедитесь, что uvicorn и matching_service запущены в отдельных терминалах
    asyncio.run(main())