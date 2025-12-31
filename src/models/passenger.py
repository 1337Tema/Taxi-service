"""
SQLAlchemy-модель пассажира.
Связана один-к-одному с таблицей users.
"""

from __future__ import annotations
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.user import User


class Passenger(Base):
    """
    Модель пассажира — профиль пользователя с ролью passenger.
    """
    __tablename__ = "passengers"

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    user: Mapped[User] = relationship(
        User,
        backref="passenger_profile",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Passenger user_id={self.id}>"
