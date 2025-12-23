"""
SQLAlchemy-модель поездки (Ride).
Содержит статус, координаты начала и конца, назначенного водителя.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Integer,
    BigInteger,
    ForeignKey,
    String,
    DECIMAL,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.db import Base
from src.models.user import User


class RideStatusEnum(str, Enum):
    """Статусы поездки."""
    PENDING = "pending"
    DRIVER_ASSIGNED = "driver_assigned"
    DRIVER_ARRIVED = "driver_arrived"
    PASSENGER_ONBOARD = "passenger_onboard"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Ride(Base):
    """
    Модель поездки.
    """
    __tablename__ = "rides"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    passenger_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    driver_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RideStatusEnum.PENDING.value
    )

    start_x: Mapped[int] = mapped_column(Integer, nullable=False)
    start_y: Mapped[int] = mapped_column(Integer, nullable=False)
    end_x: Mapped[int] = mapped_column(Integer, nullable=False)
    end_y: Mapped[int] = mapped_column(Integer, nullable=False)

    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # связи
    passenger: Mapped[User] = relationship(
        User,
        foreign_keys=[passenger_user_id],
        lazy="joined",
        backref="rides_as_passenger"
    )
    driver: Mapped[User] = relationship(
        User,
        foreign_keys=[driver_user_id],
        lazy="joined",
        backref="rides_as_driver"
    )

    def __repr__(self) -> str:
        return f"<Ride id={self.id} status={self.status} passenger={self.passenger_user_id} driver={self.driver_user_id}>"
