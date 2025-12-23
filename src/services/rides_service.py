"""
Сервис для управления поездками (Rides).
- создание поездки
- назначение водителя
- обновление статуса
- история поездок
- публикация событий OrderCreated / DriverAssigned / RideCompleted
"""

from typing import Dict, Any, List
from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ride import Ride, RideStatusEnum
from src.schemas.ride import (
    RideCreateSchema,
    RideResponseSchema,
)
from src.services.pricing_service import calculate_price_and_eta
from src.services.redis_publisher import (
    publish_order_created,
    publish_driver_assigned,
    publish_ride_completed,
)


def _build_ride_response(ride: Ride) -> RideResponseSchema:
    """Строит и возвращает схему RideResponseSchema из модели Ride."""
    return RideResponseSchema(
        ride_id=str(ride.id),
        estimated_price=float(ride.price),
        status=ride.status,
        
        start_x=ride.start_x,
        start_y=ride.start_y,
        end_x=ride.end_x,
        end_y=ride.end_y
    )


async def create_ride(
    ride_data: RideCreateSchema,
    passenger_user_id: int,
    db: AsyncSession
) -> RideResponseSchema:
    """Создает новую поездку и публикует событие OrderCreated."""

    pricing = calculate_price_and_eta(
        start_x=ride_data.start_x,
        start_y=ride_data.start_y,
        end_x=ride_data.end_x,
        end_y=ride_data.end_y,
    )

    new_ride = Ride(
        passenger_user_id=passenger_user_id,
        start_x=ride_data.start_x,
        start_y=ride_data.start_y,
        end_x=ride_data.end_x,
        end_y=ride_data.end_y,
        status=RideStatusEnum.PENDING.value,
        price=pricing["price"],
    )
    db.add(new_ride)
    await db.commit()
    await db.refresh(new_ride)

    # Публикация OrderCreated
    payload: Dict[str, Any] = {
        "ride_id": str(new_ride.id),
        "passenger_user_id": str(new_ride.passenger_user_id),
        "start_x": new_ride.start_x,
        "start_y": new_ride.start_y,
        "end_x": new_ride.end_x,
        "end_y": new_ride.end_y,
        "price": float(pricing["price"]),
        "eta_seconds": float(pricing["eta_seconds"]),
        "status": new_ride.status,
        "created_at": new_ride.created_at.isoformat() if new_ride.created_at else None
    }

    try:
        await publish_order_created(payload)
    except Exception:
        pass

    return _build_ride_response(new_ride)


async def assign_driver(
    ride_id: str,
    driver_user_id: int,
    db: AsyncSession
) -> RideResponseSchema:
    """Назначает водителя на поездку и публикует событие DriverAssigned."""

    ride = await db.get(Ride, int(ride_id))
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Поездка не найдена")

    # НОВОЕ: Проверка статуса. Принять можно только ожидающий заказ.
    if ride.status != RideStatusEnum.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Невозможно принять заказ. Его текущий статус: '{ride.status}'"
        )
    
    ride.driver_user_id = driver_user_id
    ride.status = RideStatusEnum.DRIVER_ASSIGNED.value
    ride.version += 1

    await db.commit()
    await db.refresh(ride)

    # Публикуем DriverAssigned
    payload = {
        "ride_id": str(ride.id),
        "driver_user_id": str(driver_user_id),
        "status": ride.status
    }
    try:
        await publish_driver_assigned(payload)
    except Exception:
        pass

    return _build_ride_response(ride)


async def update_ride_status(
    ride_id: str,
    new_status: str,
    db: AsyncSession
) -> RideResponseSchema:
    """Обновляет статус поездки и публикует событие RideCompleted, если применимо."""

    ride = await db.get(Ride, int(ride_id))
    if not ride:
        raise ValueError("Ride not found")

    ride.status = new_status
    ride.version += 1
    await db.commit()
    await db.refresh(ride)

    # Если поездка завершена → публикуем RideCompleted
    if new_status == RideStatusEnum.COMPLETED.value:
        payload = {
            "ride_id": str(ride.id),
            "status": ride.status
        }
        try:
            await publish_ride_completed(payload)
        except Exception:
            pass

    return _build_ride_response(ride)


async def get_user_rides(
    user_id: int,
    db: AsyncSession
) -> List[RideResponseSchema]:
    """Возвращает историю поездок пользователя."""

    result = await db.execute(
        select(Ride).where(Ride.passenger_user_id == user_id)
    )
    rides = result.scalars().all()

    return [_build_ride_response(r) for r in rides]
