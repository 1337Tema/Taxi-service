# app/location.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import schemas, dependencies, services
from .database import get_db
from .redis import get_redis
import redis

router = APIRouter(prefix="/location", tags=["location"])

@router.get("/drivers/nearby")
async def get_nearby_drivers(
    x: int,
    y: int,
    radius: int = 10,
    redis_client: redis.Redis = Depends(get_redis),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Поиск водителей поблизости"""
    if not services.validate_coordinates(x, y):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid coordinates"
        )
    
    nearby_drivers = services.find_nearby_drivers(redis_client, x, y, radius)
    return {"drivers": nearby_drivers, "count": len(nearby_drivers)}

@router.get("/rides/{ride_id}/eta")
async def get_ride_eta(
    ride_id: int,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    """Получение ETA для поездки"""
    eta_info = services.calculate_current_eta(db, redis_client, ride_id)
    if not eta_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found or no driver assigned"
        )
    
    return eta_info