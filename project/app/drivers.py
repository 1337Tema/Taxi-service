# app/drivers.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from . import schemas, crud, dependencies, services
from .database import get_db
from .redis import get_redis
import redis

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.put("/{driver_id}/status", response_model=schemas.DriverResponse)
async def update_driver_status(
    driver_id: int,
    status_update: schemas.DriverStatusUpdate,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Обновление статуса водителя (online/offline)"""
    # Проверяем права доступа
    if current_user.user_type != schemas.UserType.DRIVER or current_user.id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Обновляем статус в базе
    driver = crud.update_driver_status(db, driver_id, status_update.status)
    
    if status_update.status == schemas.DriverStatus.ONLINE:
        # Добавляем водителя в онлайн список
        if status_update.current_x is not None and status_update.current_y is not None:
            services.update_driver_location(
                redis_client, driver_id, 
                status_update.current_x, status_update.current_y
            )
        services.add_online_driver(redis_client, driver_id)
        
        # Проверяем есть ли заказы в очереди
        await services.check_pending_orders(redis_client, db, driver_id)
    
    elif status_update.status == schemas.DriverStatus.OFFLINE:
        # Убираем водителя из онлайн списка
        services.remove_online_driver(redis_client, driver_id)
        services.remove_driver_location(redis_client, driver_id)
    
    return driver

@router.put("/{driver_id}/location", response_model=dict)
async def update_driver_location(
    driver_id: int,
    location: schemas.LocationUpdate,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Обновление местоположения водителя"""
    # Проверяем права доступа
    if current_user.user_type != schemas.UserType.DRIVER or current_user.id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Проверяем валидность координат
    if not services.validate_coordinates(location.x, location.y):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid coordinates"
        )
    
    # Обновляем местоположение
    services.update_driver_location(redis_client, driver_id, location.x, location.y)
    
    # Если у водителя есть активная поездка, обновляем ETA
    active_ride = crud.get_active_driver_ride(db, driver_id)
    if active_ride:
        await services.update_ride_eta(db, redis_client, active_ride.id)
    
    return {"message": "Location updated successfully", "x": location.x, "y": location.y}

@router.get("/{driver_id}/active-ride", response_model=Optional[schemas.RideResponse])
async def get_active_ride(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Получение активной поездки водителя"""
    if current_user.user_type != schemas.UserType.DRIVER or current_user.id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return crud.get_active_driver_ride(db, driver_id)

@router.post("/{driver_id}/rides/{ride_id}/accept", response_model=schemas.RideResponse)
async def accept_ride(
    driver_id: int,
    ride_id: int,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Водитель принимает заказ"""
    if current_user.user_type != schemas.UserType.DRIVER or current_user.id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    ride = crud.accept_ride(db, ride_id, driver_id)
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ride cannot be accepted"
        )
    
    # Убираем блокировку
    services.remove_driver_lock(redis_client, driver_id)
    
    # Уведомляем пассажира
    await services.notify_passenger_ride_accepted(redis_client, ride_id, driver_id)
    
    return ride

@router.post("/{driver_id}/rides/{ride_id}/reject", response_model=dict)
async def reject_ride(
    driver_id: int,
    ride_id: int,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Водитель отклоняет заказ"""
    if current_user.user_type != schemas.UserType.DRIVER or current_user.id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    success = crud.reject_ride(db, ride_id, driver_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ride cannot be rejected"
        )
    
    # Убираем блокировку и ищем следующего водителя
    services.remove_driver_lock(redis_client, driver_id)
    await services.find_next_driver_for_ride(db, redis_client, ride_id)
    
    return {"message": "Ride rejected successfully"}

@router.get("/{driver_id}/rides", response_model=List[schemas.RideResponse])
async def get_driver_rides(
    driver_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """История поездок водителя"""
    if current_user.user_type != schemas.UserType.DRIVER or current_user.id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return crud.get_driver_rides(db, driver_id, skip=skip, limit=limit)