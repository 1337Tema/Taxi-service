"""Pydantic схемы для сущностей, связанных с водителем."""

from enum import Enum
from pydantic import BaseModel, Field, conint

from src.core.config import settings


class DriverStatus(str, Enum):
    """
    Перечисление возможных статусов водителя.

    - OFFLINE: Водитель не на линии, не участвует в поиске заказов.
    - ONLINE: Водитель на линии, готов принимать заказы.
    - BUSY: Водитель выполняет заказ.
    """
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"


class DriverLocationSchema(BaseModel):
    """Схема для координат водителя."""
    x: conint(ge=0, lt=settings.CITY_GRID_N) = Field(
        ...,
        description=f"Координата X. Должна быть в диапазоне [0, {settings.CITY_GRID_N-1}]."
    )

    y: conint(ge=0, lt=settings.CITY_GRID_M) = Field(
        ...,
        description=f"Координата Y. Должна быть в диапазоне [0, {settings.CITY_GRID_M-1}]."
    )


class DriverPresenceSchema(BaseModel):
    """
    Схема для обновления присутствия (статуса и местоположения) водителя.
    Используется в теле запроса PUT /api/v1/drivers/me/presence.
    """
    status: DriverStatus = Field(
        ...,
        description="Новый статус водителя."
    )
    
    location: DriverLocationSchema = Field(
        ...,
        description="Текущее местоположение водителя."
    )