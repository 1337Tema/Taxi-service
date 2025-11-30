# НОВОЕ
"""
Pydantic схемы для работы с заказами (rides).
"""

from pydantic import BaseModel, Field, conint
from typing import Literal


class RideCreateSchema(BaseModel):
    """
    Схема запроса для создания новой поездки.
    """
    start_x: conint(ge=0) = Field(..., description="Координата X точки подачи")
    start_y: conint(ge=0) = Field(..., description="Координата Y точки подачи")
    end_x: conint(ge=0) = Field(..., description="Координата X точки назначения")
    end_y: conint(ge=0) = Field(..., description="Координата Y точки назначения")


class RideResponseSchema(BaseModel):
    """
    Схема ответа для информации о поездке.
    """
    ride_id: str = Field(..., description="Уникальный идентификатор поездки")
    estimated_price: float = Field(..., description="Предварительная стоимость поездки")
    status: str = Field(..., description="Текущий статус поездки")


class RideStatusUpdateSchema(BaseModel):
    """
    Схема запроса для обновления статуса поездки.
    """
    status: Literal[
        "pending",
        "driver_assigned",
        "driver_arrived",
        "passenger_onboard",
        "in_progress",
        "completed",
        "cancelled"
    ] = Field(..., description="Новый статус поездки")
