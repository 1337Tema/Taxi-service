"""Модуль для управления настройками приложения с использованием Pydantic."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ConfigDict
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    """
    Класс для хранения и валидации настроек приложения.
    Настройки загружаются из переменных окружения.
    """
    
    # Настройки базы данных PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    

    @property
    def database_url_asyncpg(self) -> str:
        """Генерирует URL для асинхронного подключения к БД."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


    # Настройки Redis
    REDIS_HOST: str
    REDIS_PORT: int

    # Настройки сетки города
    CITY_GRID_N: int = 100
    CITY_GRID_M: int = 100
    
    # JWT Настройки
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Параметры ценообразования
    PRICE_BASE_FARE: float = 50.0       # базовая стоимость
    PRICE_PER_CELL: float = 5.0         # стоимость за 1 ячейку (манхэттен)
    PRICE_T_CELL: float = 10.0          # время (в секундах) на 1 ячейку

    model_config = ConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
