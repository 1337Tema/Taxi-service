"""Unit-тесты для DriverProfileService."""

import pytest
from fakeredis.aioredis import FakeRedis

from src.schemas.driver import DriverPresenceSchema, DriverLocationSchema, DriverStatus
from src.services.driver_profile_service import DriverProfileService

# Помечаем все тесты в этом модуле как асинхронные
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def redis_client() -> FakeRedis:
    """Фикстура для предоставления чистого in-memory Redis клиента для каждого теста."""
    client = FakeRedis(decode_responses=True)
    yield client
    await client.flushall()


@pytest.fixture
def driver_profile_service(redis_client: FakeRedis) -> DriverProfileService:
    """Фикстура для создания экземпляра DriverProfileService."""
    return DriverProfileService(redis=redis_client)


async def test_update_presence_new_driver_goes_online(
    driver_profile_service: DriverProfileService,
    redis_client: FakeRedis
):
    """
    Тест-кейс: Новый водитель впервые выходит на линию.

    Ожидаемый результат:
    1. Геоиндекс `cell:X:Y` содержит ID водителя.
    2. Местоположение водителя сохранено в ключе `driver_location:{id}`.
    """
    # Arrange: Готовим тестовые данные
    driver_id = 101
    presence_data = DriverPresenceSchema(
        status=DriverStatus.ONLINE,
        location=DriverLocationSchema(x=15, y=20)
    )

    # Act: Вызываем тестируемый метод
    await driver_profile_service.update_presence(driver_id, presence_data)

    # Assert: Проверяем состояние Redis
    cell_key = "cell:15:20"
    location_key = f"driver_location:{driver_id}"

    # Проверяем, что водитель появился в нужной ячейке
    drivers_in_cell = await redis_client.hgetall(cell_key)
    assert drivers_in_cell == {str(driver_id): "online"}

    # Проверяем, что его текущая локация сохранена
    saved_location = await redis_client.get(location_key)
    assert saved_location == "15:20"


async def test_update_presence_driver_moves_to_new_location(
    driver_profile_service: DriverProfileService,
    redis_client: FakeRedis
):
    """
    Тест-кейс: Водитель, уже будучи онлайн, перемещается в новую ячейку.

    Ожидаемый результат:
    1. ID водителя удален из старой ячейки `cell:X_old:Y_old`.
    2. ID водителя добавлен в новую ячейку `cell:X_new:Y_new`.
    3. Ключ `driver_location:{id}` обновлен.
    """
    # Arrange: Готовим начальное состояние
    driver_id = 102
    old_location = (x, y) = (5, 5)
    old_cell_key = f"cell:{x}:{y}"
    location_key = f"driver_location:{driver_id}"
    await redis_client.hset(old_cell_key, str(driver_id), "online")
    await redis_client.set(location_key, f"{x}:{y}")

    # Готовим новые данные
    new_presence_data = DriverPresenceSchema(
        status=DriverStatus.ONLINE,
        location=DriverLocationSchema(x=10, y=12)
    )
    new_cell_key = "cell:10:12"

    # Act
    await driver_profile_service.update_presence(driver_id, new_presence_data)

    # Assert
    # Проверяем, что водителя больше нет в старой ячейке
    drivers_in_old_cell = await redis_client.hgetall(old_cell_key)
    assert str(driver_id) not in drivers_in_old_cell

    # Проверяем, что водитель появился в новой ячейке
    drivers_in_new_cell = await redis_client.hgetall(new_cell_key)
    assert drivers_in_new_cell == {str(driver_id): "online"}

    # Проверяем, что локация обновлена
    saved_location = await redis_client.get(location_key)
    assert saved_location == "10:12"


async def test_update_presence_driver_goes_offline(
    driver_profile_service: DriverProfileService,
    redis_client: FakeRedis
):
    """
    Тест-кейс: Водитель уходит с линии (становится offline).

    Ожидаемый результат:
    1. ID водителя удален из ячейки, где он был.
    2. Ключ `driver_location:{id}` удален.
    """
    # Arrange: Готовим начальное состояние
    driver_id = 103
    location = (x, y) = (25, 30)
    cell_key = f"cell:{x}:{y}"
    location_key = f"driver_location:{driver_id}"
    await redis_client.hset(cell_key, str(driver_id), "online")
    await redis_client.set(location_key, f"{x}:{y}")

    # Готовим данные для обновления (статус offline)
    offline_presence_data = DriverPresenceSchema(
        status=DriverStatus.OFFLINE,
        location=DriverLocationSchema(x=x, y=y) # локация не важна, но должна быть валидной
    )

    # Act
    await driver_profile_service.update_presence(driver_id, offline_presence_data)

    # Assert Проверяем, что водителя больше нет в ячейке
    drivers_in_cell = await redis_client.hgetall(cell_key)
    assert str(driver_id) not in drivers_in_cell

    # Проверяем, что ключ с локацией удален
    location_exists = await redis_client.exists(location_key)
    assert not location_exists