# app/services.py
from sqlalchemy.orm import Session
import redis
import asyncio
from typing import List, Optional
from . import crud, schemas
from .config import settings

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

connection_manager = ConnectionManager()

def validate_coordinates(x: int, y: int) -> bool:
    """Проверка валидности координат"""
    return (0 <= x < settings.GRID_SIZE_X and 
            0 <= y < settings.GRID_SIZE_Y)

def calculate_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Расчет расстояния по манхэттенской метрике"""
    return abs(x1 - x2) + abs(y1 - y2)

def calculate_price_and_eta(start_x: int, start_y: int, end_x: int, end_y: int) -> schemas.PriceCalculation:
    """Расчет цены и ETA для поездки"""
    distance = calculate_distance(start_x, start_y, end_x, end_y)
    estimated_duration = distance * settings.TIME_PER_CELL
    estimated_price = settings.BASE_FARE + (distance * settings.PRICE_PER_CELL)
    estimated_price = max(estimated_price, settings.MIN_FARE)
    
    return schemas.PriceCalculation(
        distance=distance,
        estimated_duration=estimated_duration,
        estimated_price=estimated_price
    )

async def find_driver_for_ride(db: Session, redis_client: redis.Redis, ride_id: int):
    """Поиск водителя для заказа"""
    ride = crud.get_ride(db, ride_id)
    if not ride or ride.status != schemas.RideStatus.PENDING:
        return
    
    # Ищем ближайших водителей
    nearby_drivers = find_nearby_drivers(
        redis_client, ride.start_x, ride.start_y, settings.SEARCH_RADIUS
    )
    
    if not nearby_drivers:
        # Добавляем в очередь
        redis_client.lpush("pending_orders", ride_id)
        await notify_passenger_no_drivers(redis_client, ride.passenger_id)
        return
    
    # Пытаемся назначить водителей по очереди
    for driver_id in nearby_drivers:
        if await assign_ride_to_driver(db, redis_client, ride_id, driver_id):
            break

async def assign_ride_to_driver(db: Session, redis_client: redis.Redis, ride_id: int, driver_id: int) -> bool:
    """Назначение заказа водителю"""
    # Проверяем, не заблокирован ли водитель
    if is_driver_locked(redis_client, driver_id):
        return False
    
    # Блокируем водителя на время ожидания ответа
    lock_driver(redis_client, driver_id, ride_id)
    
    # Отправляем уведомление водителю
    await notify_driver_new_ride(redis_client, driver_id, ride_id)
    
    # Запускаем таймер ожидания ответа
    asyncio.create_task(wait_for_driver_response(db, redis_client, ride_id, driver_id))
    
    return True

async def wait_for_driver_response(db: Session, redis_client: redis.Redis, ride_id: int, driver_id: int):
    """Ожидание ответа от водителя"""
    await asyncio.sleep(settings.DRIVER_RESPONSE_TIMEOUT)
    
    # Проверяем, принял ли водитель заказ
    ride = crud.get_ride(db, ride_id)
    if ride and ride.status == schemas.RideStatus.PENDING:
        # Водитель не ответил, ищем следующего
        remove_driver_lock(redis_client, driver_id)
        await find_next_driver_for_ride(db, redis_client, ride_id)