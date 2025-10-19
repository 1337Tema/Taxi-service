# app/passengers.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from . import schemas, crud, dependencies, services
from .database import get_db
from .redis import get_redis
import redis

router = APIRouter(prefix="/passengers", tags=["passengers"])

@router.post("/{passenger_id}/rides", response_model=schemas.RideResponse)
async def create_ride(
    passenger_id: int,
    ride_data: schemas.RideCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Создание нового заказа такси"""
    # Проверяем права доступа
    if current_user.user_type != schemas.UserType.PASSENGER or current_user.id != passenger_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Проверяем валидность координат
    if not services.validate_coordinates(ride_data.start_x, ride_data.start_y) or \
       not services.validate_coordinates(ride_data.end_x, ride_data.end_y):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid coordinates"
        )
    
    # Проверяем, нет ли активной поездки
    active_ride = crud.get_active_passenger_ride(db, passenger_id)
    if active_ride:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active ride"
        )
    
    # Рассчитываем цену и ETA
    price_info = services.calculate_price_and_eta(
        ride_data.start_x, ride_data.start_y,
        ride_data.end_x, ride_data.end_y
    )
    
    # Создаем поездку
    ride = crud.create_ride(db, ride_data, price_info)
    
    # Запускаем поиск водителя в фоне
    background_tasks.add_task(
        services.find_driver_for_ride, db, redis_client, ride.id
    )
    
    return ride

@router.get("/{passenger_id}/active-ride", response_model=Optional[schemas.RideResponse])
async def get_active_ride(
    passenger_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Получение активной поездки пассажира"""
    if current_user.user_type != schemas.UserType.PASSENGER or current_user.id != passenger_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return crud.get_active_passenger_ride(db, passenger_id)

@router.put("/{passenger_id}/rides/{ride_id}/status", response_model=schemas.RideResponse)
async def update_ride_status(
    passenger_id: int,
    ride_id: int,
    status_update: schemas.RideStatusUpdate,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Обновление статуса поездки"""
    if current_user.user_type != schemas.UserType.PASSENGER or current_user.id != passenger_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    ride = crud.update_ride_status(db, ride_id, status_update.status)
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update ride status"
        )
    
    # Уведомляем водителя об изменении статуса
    if ride.driver_id:
        await services.notify_driver_ride_status_update(redis_client, ride_id, status_update.status)
    
    return ride

@router.post("/{passenger_id}/rides/{ride_id}/cancel", response_model=schemas.RideResponse)
async def cancel_ride(
    passenger_id: int,
    ride_id: int,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Отмена поездки пассажиром"""
    if current_user.user_type != schemas.UserType.PASSENGER or current_user.id != passenger_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    ride = crud.cancel_ride(db, ride_id)
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel ride"
        )
    
    # Если есть назначенный водитель, уведомляем его
    if ride.driver_id:
        await services.notify_driver_ride_cancelled(redis_client, ride_id, ride.driver_id)
        services.remove_driver_lock(redis_client, ride.driver_id)
    
    return ride

@router.get("/{passenger_id}/rides", response_model=List[schemas.RideResponse])
async def get_passenger_rides(
    passenger_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """История поездок пассажира"""
    if current_user.user_type != schemas.UserType.PASSENGER or current_user.id != passenger_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return crud.get_passenger_rides(db, passenger_id, skip=skip, limit=limit)