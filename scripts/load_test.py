"""
Простой скрипт для нагрузочного тестирования.
Адаптирован для Windows: сняты лимиты подключений.
"""
import asyncio
import httpx
import random
import time
import redis.asyncio as aioredis
import uuid

# --- Настройки ---
BASE_URL = "http://127.0.0.1:8000/api/v1"
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

NUM_DRIVERS = 100   
GRID_N = 100
GRID_M = 100

HEARTBEAT_REQUESTS = 1000
MATCHING_REQUESTS = 100    


async def setup_drivers(redis_client):
    """Создает водителей в Redis."""
    print(f"--- 1. Создание {NUM_DRIVERS} водителей в Redis... ---")
    pipe = redis_client.pipeline()
    await redis_client.flushdb()

    for i in range(1, NUM_DRIVERS + 1):
        x, y = random.randint(0, GRID_N - 1), random.randint(0, GRID_M - 1)
        cell_key = f"cell:{x}:{y}"
        location_key = f"driver_location:{i}"
        
        pipe.hset(cell_key, str(i), "online")
        pipe.set(location_key, f"{x}:{y}")

    await pipe.execute()
    print("✅ Водители размещены на карте.")


async def run_heartbeat_test():
    """Тестирует эндпоинт обновления присутствия."""
    print(f"\n--- 2. Запуск {HEARTBEAT_REQUESTS} Heartbeat-запросов (PUT)... ---")
    
    limits = httpx.Limits(max_keepalive_connections=None, max_connections=None)
    timeout = httpx.Timeout(30.0, connect=30.0)

    async with httpx.AsyncClient(trust_env=False, limits=limits, timeout=timeout) as client:
        tasks = []
        for _ in range(HEARTBEAT_REQUESTS):
            payload = {
                "status": "online",
                "location": {
                    "x": random.randint(0, GRID_N - 1),
                    "y": random.randint(0, GRID_M - 1),
                }
            }
            # Фейковый токен
            headers = {"Authorization": f"Bearer load_test_{uuid.uuid4()}"}
            
            tasks.append(client.put(
                f"{BASE_URL}/drivers/me/presence", 
                json=payload,
                headers=headers
            ))

        start_time = time.monotonic()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.monotonic()

        total_time = end_time - start_time
        
        success_count = len([r for r in responses if not isinstance(r, Exception)])
        error_count = len(responses) - success_count

        print(f"Всего запросов: {len(responses)}")
        print(f"Успешно отправлено (ответ получен): {success_count}")
        print(f"Ошибок соединения/таймаута: {error_count}")
        print(f"Время выполнения: {total_time:.2f} сек.")
        
        if total_time > 0:
            print(f"RPS (Requests Per Second): {len(responses) / total_time:.2f}")


async def run_matching_test(redis_client):
    """Кидает заказы напрямую в Redis Stream."""
    print(f"\n--- 3. Отправка {MATCHING_REQUESTS} заказов в очередь... ---")

    tasks = []
    for i in range(MATCHING_REQUESTS):
        ride_id = f"load_test_ride_{i}"
        payload = {
            "ride_id": ride_id,
            "start_x": str(random.randint(0, GRID_N - 1)),
            "start_y": str(random.randint(0, GRID_M - 1)),
        }
        tasks.append(redis_client.xadd("order_events", payload))

    start_time = time.monotonic()
    await asyncio.gather(*tasks)
    end_time = time.monotonic()

    print(f"Заказы отправлены за {end_time - start_time:.2f} сек.")
    print("👀 Смотри во второе окно терминала (где run_matching_service), там должны побежать логи обработки!")


async def main():
    redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    try:
        await redis_client.ping()
        print("✅ Подключение к Redis успешно.")
    except Exception as e:
        print(f"❌ Не могу подключиться к Redis: {e}")
        return

    await setup_drivers(redis_client)
    await run_heartbeat_test()
    await run_matching_test(redis_client)
    
    await redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())