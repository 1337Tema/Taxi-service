# ИЗМЕНЕНО
"""
Эндпоинты для работы с поездками (rides).
Добавлены: accept, update_status, history.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.schemas.ride import (
    RideCreateSchema,
    RideResponseSchema,
    RideStatusUpdateSchema,
)
from src.core.db import get_async_session
from src.api.v1.dependencies import get_current_user_id

from src.services.rides_service import (
    create_ride as create_ride_service,
    assign_driver as assign_driver_service,
    update_ride_status as update_status_service,
    get_user_rides as get_user_rides_service,
)

router = APIRouter(prefix="/rides", tags=["Rides"])


# POST /rides — создание заказа
@router.post("", response_model=RideResponseSchema)
async def create_ride(
    ride_data: RideCreateSchema,
    db: AsyncSession = Depends(get_async_session),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        return await create_ride_service(
            ride_data=ride_data,
            passenger_user_id=current_user_id,
            db=db
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# POST /rides/{id}/accept — водитель принимает заказ
@router.post("/{ride_id}/accept", response_model=RideResponseSchema)
async def accept_ride(
    ride_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        return await assign_driver_service(
            ride_id=str(ride_id),
            driver_user_id=current_user_id,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as exc:
        print(f"Error accepting ride: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# PUT /rides/{id}/status — обновление статуса (оба могут)
@router.put("/{ride_id}/status", response_model=RideResponseSchema)
async def update_ride_status(
    ride_id: int,
    status_update: RideStatusUpdateSchema,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        return await update_status_service(
            ride_id=str(ride_id),
            new_status=status_update.status,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as exc:
        print(f"Error updating status: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# GET /rides/history — история поездок
@router.get("/history", response_model=List[RideResponseSchema])
async def get_user_rides(
    db: AsyncSession = Depends(get_async_session),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        return await get_user_rides_service(
            user_id=current_user_id,
            db=db
        )
    except Exception as exc:
        print(f"Error getting history: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
