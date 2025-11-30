# НОВОЕ
"""
SQLAlchemy-модели для сущности User.
Содержит базовые поля для аутентификации и разграничения ролей.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class User(Base):
    """
    Модель пользователя в системе.
    Используется и для пассажиров, и для водителей, и для админов.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )  # ИЗМЕНЕНО: id теперь primary key

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )  # НОВОЕ: уникальный email

    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # НОВОЕ: пароль хранится только в хэшированном виде

    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="passenger"
    )  # НОВОЕ: роли system-level: passenger / driver / admin

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # НОВОЕ

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )  # НОВОЕ

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
