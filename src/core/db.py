""""Модуль для настройки асинхронного взаимодействия с базой данных с использованием SQLAlchemy."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# Создаем асинхронный "движок" для взаимодействия с базой данных
engine = create_async_engine(
    settings.database_url_asyncpg,
    echo=False,
    pool_pre_ping=True,
)

# Фабрика для создания асинхронных сессий
async_session_maker = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""
    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Функция-зависимость для FastAPI для получения асинхронной сессии БД.
    Обеспечивает корректное открытие и закрытие сессии для каждого запроса.
    """
    async with async_session_maker() as session:
        yield session