# 🚀 Руководство по запуску и тестированию Taxi Grid Service

## 📋 Содержание
1. [Предварительные требования](#предварительные-требования)
2. [Быстрый старт](#быстрый-старт)
3. [Подробная инструкция по запуску](#подробная-инструкция-по-запуску)
4. [Тестирование функциональности](#тестирование-функциональности)
5. [API документация и примеры](#api-документация-и-примеры)
6. [Нагрузочное тестирование](#нагрузочное-тестирование)
7. [Отладка и логи](#отладка-и-логи)
8. [Часто встречающиеся проблемы](#часто-встречающиеся-проблемы)

## 🔧 Предварительные требования

### Системные требования:
- **Docker** и **Docker Compose** (версия 3.8+)
- **Python 3.11+** (для локальной разработки)
- **Git** для клонирования репозитория
- **curl** или **Postman** для тестирования API

### Проверка установки:
```bash
docker --version          # Docker version 20.10+
docker-compose --version  # docker-compose version 1.29+
python --version          # Python 3.11+
```

## ⚡ Быстрый старт

### 1. Клонирование и запуск
```bash
# Клонируем репозиторий
git clone <repository-url>
cd taxi-service

# Убеждаемся, что есть необходимые файлы
# (docker-compose.yml и .env должны быть в корне проекта)

# Запускаем все сервисы
docker-compose up -d

# Проверяем статус
docker-compose ps
```

### 2. Проверка работоспособности
```bash
# Проверяем API
curl http://localhost:8000/healthcheck

# Ожидаемый ответ: {"status": "ok"}

# Проверяем доступность всех эндпоинтов
python scripts/test_endpoints.py
```

### 3. Применение миграций
```bash
# Заходим в контейнер API
docker-compose exec api bash

# Применяем миграции
alembic upgrade head

# Выходим из контейнера
exit
```

## 📖 Подробная инструкция по запуску

### Шаг 1: Подготовка окружения

#### Локальная разработка (опционально):
```bash
# Создаем виртуальное окружение
python -m venv .venv

# Активируем (Windows)
.venv\Scripts\activate

# Активируем (Linux/Mac)
source .venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

#### Настройка переменных окружения:
```bash
# Файл .env уже должен существовать в корне проекта
# При необходимости можно отредактировать
nano .env

# Основные переменные:
# POSTGRES_USER=taxi_user
# POSTGRES_PASSWORD=noRE13t4U
# POSTGRES_DB=taxi_db
# JWT_SECRET_KEY=a_very_secret_key_for_tests
```

### Шаг 2: Запуск инфраструктуры

#### Запуск через Docker Compose:
```bash
# Запуск в фоновом режиме
docker-compose up -d

# Запуск с логами (для отладки)
docker-compose up

# Запуск только определенных сервисов
docker-compose up -d db redis
```

#### Проверка сервисов:
```bash
# Статус всех контейнеров
docker-compose ps

# Логи конкретного сервиса
docker-compose logs api
docker-compose logs db
docker-compose logs redis

# Следим за логами в реальном времени
docker-compose logs -f api
```

### Шаг 3: Инициализация базы данных

```bash
# Заходим в контейнер API
docker-compose exec api bash

# Применяем миграции
alembic upgrade head

# Проверяем таблицы (опционально)
docker-compose exec db psql -U taxi_user -d taxi_db -c "\dt"
```

### Шаг 4: Запуск Matching Service

Matching Service должен запускаться отдельно для обработки заказов:

```bash
# В отдельном терминале
docker-compose exec api python src/run_matching_service.py

# Или локально (если установлены зависимости)
python src/run_matching_service.py
```

## 🧪 Тестирование функциональности

### 1. Проверка эндпоинтов

```bash
# Сначала проверяем, что все эндпоинты доступны
python scripts/test_endpoints.py

# Ожидаемый вывод:
# ✅ GET /healthcheck - Проверка здоровья: OK
# ✅ POST /api/v1/auth/register - Регистрация: OK (требует данные/авторизацию)
# ✅ POST /api/v1/auth/login - Логин: OK (требует данные/авторизацию)
```

### 2. Автоматический тест аутентификации

```bash
# Запускаем тест аутентификации
python scripts/test_auth.py

# Ожидаемый вывод:
# ✅ Регистрация успешна
# ✅ Логин успешен
# ✅ Защищенный эндпоинт работает
# ✅ Защита работает: запрос без токена отклонен
```

### 3. Unit тесты

```bash
# Запуск всех тестов
docker-compose exec api pytest

# Запуск конкретного теста
docker-compose exec api pytest tests/services/test_driver_profile_service.py -v

# Запуск с покрытием
docker-compose exec api pytest --cov=src tests/
```

### 4. Ручное тестирование API

#### 3.1 Регистрация пользователя
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "driver1@example.com",
    "password": "password123"
  }'

# Ответ:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "token_type": "bearer"
# }
```

#### 3.2 Логин
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "driver1@example.com",
    "password": "password123"
  }'
```

#### 3.3 Обновление статуса водителя
```bash
# Сохраняем токен в переменную
TOKEN="your_jwt_token_here"

curl -X PUT http://localhost:8000/api/v1/drivers/me/presence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "online",
    "location": {
      "x": 10,
      "y": 15
    }
  }'

# Ожидаемый ответ: HTTP 204 No Content
```

#### 3.4 Создание заказа
```bash
# Регистрируем пассажира
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "passenger1@example.com",
    "password": "password123"
  }'

# Получаем токен пассажира
PASSENGER_TOKEN="passenger_jwt_token_here"

# Создаем заказ
curl -X POST http://localhost:8000/api/v1/rides \
  -H "Authorization: Bearer $PASSENGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_x": 5,
    "start_y": 5,
    "end_x": 20,
    "end_y": 25
  }'

# Ответ:
# {
#   "ride_id": "123",
#   "estimated_price": 125.0,
#   "status": "pending"
# }
```

#### 3.5 Принятие заказа водителем
```bash
RIDE_ID="123"

curl -X POST http://localhost:8000/api/v1/rides/$RIDE_ID/accept \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

#### 3.6 История поездок
```bash
curl -X GET http://localhost:8000/api/v1/rides/history \
  -H "Authorization: Bearer $PASSENGER_TOKEN"
```

### 5. Тестирование WebSocket

#### 4.1 Подключение через JavaScript (в браузере):
```javascript
// Открываем консоль браузера на http://localhost:8000
const token = "your_jwt_token_here";
const ws = new WebSocket(`ws://localhost:8000/api/v1/notifications/ws?token=${token}`);

ws.onopen = function(event) {
    console.log("WebSocket подключен");
    ws.send("ping"); // Тест ping-pong
};

ws.onmessage = function(event) {
    console.log("Получено сообщение:", JSON.parse(event.data));
};

ws.onclose = function(event) {
    console.log("WebSocket закрыт");
};
```

#### 4.2 Тестирование через curl (для проверки HTTP Upgrade):
```bash
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
     "http://localhost:8000/api/v1/notifications/ws?token=$TOKEN"
```

## 📊 Нагрузочное тестирование

### 1. Подготовка к нагрузочному тесту
```bash
# Убеждаемся, что все сервисы запущены
docker-compose ps

# Запускаем Matching Service
docker-compose exec api python src/run_matching_service.py &
```

### 2. Запуск нагрузочного теста
```bash
# Запускаем тест производительности
python scripts/load_test.py

# Ожидаемый вывод:
# --- Создание 1000 водителей... ---
# --- Тест 1: Запуск 2000 Heartbeat-запросов... ---
# Выполнено 2000 запросов за X.XX сек.
# Успешных запросов: XXXX (XX.X%)
# RPS (Requests Per Second): XXX.XX
```

### 3. Мониторинг производительности

#### Мониторинг ресурсов:
```bash
# Использование ресурсов контейнерами
docker stats

# Логи производительности
docker-compose logs api | grep -i "performance\|time\|slow"

# Мониторинг Redis
docker-compose exec redis redis-cli monitor
```

#### Проверка Redis:
```bash
# Подключаемся к Redis
docker-compose exec redis redis-cli

# Проверяем количество водителей в ячейках
KEYS cell:*

# Проверяем события в стриме
XLEN order_events

# Проверяем активные блокировки
KEYS driver_lock:*
```

## 📋 API документация и примеры

### Swagger UI
После запуска сервиса, документация доступна по адресу:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Основные эндпоинты

| Метод | Путь | Описание | Аутентификация |
|-------|------|----------|----------------|
| POST | `/api/v1/auth/register` | Регистрация пользователя | Нет |
| POST | `/api/v1/auth/login` | Логин пользователя | Нет |
| PUT | `/api/v1/drivers/me/presence` | Обновление статуса водителя | JWT |
| POST | `/api/v1/rides` | Создание заказа | JWT |
| POST | `/api/v1/rides/{id}/accept` | Принятие заказа | JWT |
| PUT | `/api/v1/rides/{id}/status` | Обновление статуса поездки | JWT |
| GET | `/api/v1/rides/history` | История поездок | JWT |
| WS | `/api/v1/notifications/ws` | WebSocket уведомления | JWT (query) |

### Примеры полных сценариев

#### Сценарий 1: Полный цикл заказа
```bash
#!/bin/bash

# 1. Регистрация водителя
DRIVER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "driver@test.com", "password": "password123"}')

DRIVER_TOKEN=$(echo $DRIVER_RESPONSE | jq -r '.access_token')

# 2. Водитель выходит на линию
curl -X PUT http://localhost:8000/api/v1/drivers/me/presence \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "online", "location": {"x": 10, "y": 10}}'

# 3. Регистрация пассажира
PASSENGER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "passenger@test.com", "password": "password123"}')

PASSENGER_TOKEN=$(echo $PASSENGER_RESPONSE | jq -r '.access_token')

# 4. Пассажир создает заказ
RIDE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/rides \
  -H "Authorization: Bearer $PASSENGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"start_x": 8, "start_y": 8, "end_x": 15, "end_y": 15}')

RIDE_ID=$(echo $RIDE_RESPONSE | jq -r '.ride_id')

echo "Заказ создан: $RIDE_ID"

# 5. Ждем, пока Matching Service найдет водителя
sleep 5

# 6. Водитель принимает заказ
curl -X POST http://localhost:8000/api/v1/rides/$RIDE_ID/accept \
  -H "Authorization: Bearer $DRIVER_TOKEN"

echo "Заказ принят водителем"
```

## 🔍 Отладка и логи

### Просмотр логов
```bash
# Все логи
docker-compose logs

# Логи конкретного сервиса
docker-compose logs api
docker-compose logs db
docker-compose logs redis

# Логи в реальном времени
docker-compose logs -f api

# Логи с фильтрацией
docker-compose logs api | grep ERROR
docker-compose logs api | grep "JWT\|auth"
```

### Отладка базы данных
```bash
# Подключение к PostgreSQL
docker-compose exec db psql -U taxi_user -d taxi_db

# Полезные SQL запросы:
# Список таблиц
\dt

# Пользователи
SELECT id, email, role, created_at FROM users;

# Водители
SELECT d.id, u.email, d.status, d.x, d.y, d.last_online 
FROM drivers d JOIN users u ON d.id = u.id;

# Поездки
SELECT id, passenger_user_id, driver_user_id, status, start_x, start_y, end_x, end_y, price 
FROM rides ORDER BY created_at DESC LIMIT 10;
```

### Отладка Redis
```bash
# Подключение к Redis
docker-compose exec redis redis-cli

# Полезные команды:
# Все ключи
KEYS *

# Водители в ячейках
KEYS cell:*
HGETALL cell:10:10

# Блокировки водителей
KEYS driver_lock:*

# События в стриме
XLEN order_events
XRANGE order_events - + COUNT 5

# Pub/Sub каналы
PUBSUB CHANNELS
```

## ❗ Часто встречающиеся проблемы

### 1. Контейнеры не запускаются
```bash
# Проверяем порты
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379
netstat -tulpn | grep :8000

# Освобождаем порты если заняты
sudo lsof -ti:5432 | xargs kill -9
sudo lsof -ti:6379 | xargs kill -9
sudo lsof -ti:8000 | xargs kill -9

# Пересоздаем контейнеры
docker-compose down
docker-compose up -d --force-recreate
```

### 2. Ошибки миграций
```bash
# Сброс миграций
docker-compose exec api alembic downgrade base
docker-compose exec api alembic upgrade head

# Пересоздание базы данных
docker-compose down -v
docker-compose up -d
```

### 3. JWT ошибки
```bash
# Проверяем переменные окружения
docker-compose exec api env | grep JWT

# Проверяем секретный ключ
echo $JWT_SECRET_KEY
```

### 4. Redis подключение
```bash
# Проверяем подключение
docker-compose exec api python -c "
import redis.asyncio as aioredis
import asyncio
async def test():
    r = aioredis.Redis(host='redis', port=6379)
    await r.ping()
    print('Redis OK')
asyncio.run(test())
"
```

### 5. WebSocket проблемы
```bash
# Проверяем Nginx конфигурацию
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf

# Тестируем WebSocket через curl
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: test" \
     "http://localhost:8000/api/v1/notifications/ws?token=test"
```

## 🎯 Заключение

Этот проект полностью готов к тестированию и демонстрации. Все компоненты архитектуры реализованы и протестированы:

- ✅ JWT аутентификация
- ✅ Геоиндексация водителей
- ✅ Асинхронный поиск и назначение
- ✅ Real-time уведомления
- ✅ Event-driven архитектура
- ✅ Полный API для такси-сервиса

Для получения дополнительной помощи обращайтесь к документации API по адресу http://localhost:8000/docs после запуска сервиса.