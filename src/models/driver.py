"""
SQLAlchemy-модель водителя.
Связана один-к-одному с пользователем (users).
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Integer,
    ForeignKey,
    String,
    DateTime,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.db import Base
from src.core.config import settings
from src.models.user import User


class DriverStatusEnum(str, Enum):
    """Статусы водителя."""
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"


class Driver(Base):
    """
    Профиль водителя.
    Таблица хранит текущее состояние и координаты водителя.
    """
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=DriverStatusEnum.OFFLINE.value
    )

    x: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    y: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # используется для выбора водителя при равенстве расстояния
    last_online: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    user: Mapped[User] = relationship(
        User,
        backref="driver_profile",
        lazy="joined"
    )

    __table_args__ = (
        CheckConstraint(f"x >= 0 AND x < {settings.CITY_GRID_N}", name="chk_driver_x_range"),
        CheckConstraint(f"y >= 0 AND y < {settings.CITY_GRID_M}", name="chk_driver_y_range"),
    )

    def __repr__(self) -> str:
        return f"<Driver id={self.id} status={self.status} loc=({self.x},{self.y})>"
