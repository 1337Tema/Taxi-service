# Этап 1: Используем официальный образ Python
FROM python:3.11-slim AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем poetry (менеджер зависимостей)
RUN pip install poetry

# Копируем файлы для установки зависимостей
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости проекта, не включая dev-зависимости
RUN poetry config virtualenvs.create false && poetry install --without dev

# Этап 2: Создаем финальный, легковесный образ
FROM python:3.11-slim

WORKDIR /app

# Копируем установленные зависимости из builder'а
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Копируем исходный код приложения
COPY ./src .

# Указываем команду для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]