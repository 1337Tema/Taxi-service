#!/bin/bash

# Taxi Grid Service - Startup Script
# Автоматический запуск всех компонентов системы

set -e  # Выход при любой ошибке

echo "🚀 Taxi Grid Service - Автоматический запуск"
echo "============================================="

# Функция для проверки доступности порта
check_port() {
    local port=$1
    local service=$2
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        echo "⚠️  Порт $port уже занят ($service). Освободите порт или остановите сервис."
        return 1
    fi
    return 0
}

# Функция для ожидания готовности сервиса
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Ожидание готовности $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name готов!"
            return 0
        fi
        echo "   Попытка $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name не готов после $max_attempts попыток"
    return 1
}

echo ""
echo "🔍 Шаг 1: Проверка предварительных условий"
echo "==========================================="

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

echo "✅ Docker и Docker Compose установлены"

# Проверяем наличие необходимых файлов
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Файл docker-compose.yml не найден в текущей директории"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден в текущей директории"
    exit 1
fi

echo "✅ Конфигурационные файлы найдены"

# Проверяем доступность портов
echo "🔌 Проверка доступности портов..."
check_port 8000 "API" || exit 1
check_port 5432 "PostgreSQL" || exit 1
check_port 6379 "Redis" || exit 1
check_port 80 "Nginx" || exit 1

echo "✅ Все порты свободны"

echo ""
echo "🐳 Шаг 2: Запуск Docker контейнеров"
echo "==================================="

# Останавливаем существующие контейнеры (если есть)
echo "🛑 Остановка существующих контейнеров..."
docker-compose down > /dev/null 2>&1 || true

# Собираем и запускаем контейнеры
echo "🔨 Сборка и запуск контейнеров..."
docker-compose up -d --build

# Проверяем статус контейнеров
echo "📊 Статус контейнеров:"
docker-compose ps

echo ""
echo "⏳ Шаг 3: Ожидание готовности сервисов"
echo "======================================"

# Ждем готовности PostgreSQL
wait_for_service "http://localhost:5432" "PostgreSQL" || {
    echo "❌ PostgreSQL не готов. Проверьте логи: docker-compose logs db"
    exit 1
}

# Ждем готовности Redis
wait_for_service "http://localhost:6379" "Redis" || {
    echo "❌ Redis не готов. Проверьте логи: docker-compose logs redis"
    exit 1
}

# Ждем готовности API
wait_for_service "http://localhost:8000/healthcheck" "API" || {
    echo "❌ API не готов. Проверьте логи: docker-compose logs api"
    exit 1
}

echo ""
echo "🗄️  Шаг 4: Инициализация базы данных"
echo "===================================="

echo "📋 Применение миграций..."
if docker-compose exec -T api alembic upgrade head; then
    echo "✅ Миграции применены успешно"
else
    echo "❌ Ошибка при применении миграций"
    echo "💡 Попробуйте выполнить вручную: docker-compose exec api alembic upgrade head"
fi

echo ""
echo "🧪 Шаг 5: Проверка API эндпоинтов"
echo "================================="

if command -v python3 &> /dev/null; then
    echo "🔍 Проверка доступности эндпоинтов..."
    python3 scripts/test_endpoints.py
else
    echo "⚠️  Python3 не найден. Пропускаем проверку эндпоинтов."
    echo "💡 Проверьте вручную: curl http://localhost:8000/healthcheck"
fi

echo ""
echo "🎉 ЗАПУСК ЗАВЕРШЕН!"
echo "=================="
echo ""
echo "✅ Все сервисы запущены и готовы к работе:"
echo ""
echo "🌐 API:              http://localhost:8000"
echo "📚 Swagger UI:       http://localhost:8000/docs"
echo "📖 ReDoc:            http://localhost:8000/redoc"
echo "🔧 Nginx:            http://localhost:80"
echo ""
echo "🔧 Следующие шаги:"
echo ""
echo "1. 🚗 Запустите Matching Service (в отдельном терминале):"
echo "   docker-compose exec api python src/run_matching_service.py"
echo ""
echo "2. 🧪 Запустите быстрый тест:"
echo "   bash scripts/quick_test.sh"
echo ""
echo "3. 🔍 Проверьте логи при необходимости:"
echo "   docker-compose logs -f api"
echo ""
echo "4. 🛑 Для остановки всех сервисов:"
echo "   docker-compose down"
echo ""
echo "📋 Подробная документация: TESTING_GUIDE.md"
echo ""
echo "🎯 Система готова к тестированию!"