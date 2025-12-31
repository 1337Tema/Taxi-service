#!/bin/bash

# Taxi Grid Service - Quick Test Script
# Автоматический тест полного цикла с генерацией уникальных пользователей

set -e  # Выход при любой ошибке

# Генерируем случайный суффикс для уникальности email
SUFFIX=$RANDOM
DRIVER_EMAIL="driver_${SUFFIX}@test.com"
PASSENGER_EMAIL="passenger_${SUFFIX}@test.com"

# Жестко задаем адрес API (минуя Nginx и IPv6 проблемы)
API_URL="http://127.0.0.1:8000"

echo "🚀 Taxi Grid Service - Быстрый тест (Run ID: $SUFFIX)"
echo "===================================================="
echo "🎯 Целевой URL: $API_URL"

# Проверяем, что сервис запущен
echo "📡 Проверяем доступность API..."
if ! curl -s $API_URL/healthcheck > /dev/null; then
    echo "❌ API недоступен по адресу $API_URL."
    echo "   Убедитесь, что контейнеры запущены (docker-compose up -d)"
    exit 1
fi
echo "✅ API доступен"

# Функция для извлечения токена из JSON ответа
extract_token() {
    echo "$1" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
}

# Функция для извлечения ride_id из JSON ответа
extract_ride_id() {
    echo "$1" | python3 -c "import sys, json; print(json.load(sys.stdin)['ride_id'])"
}

echo ""
echo "👤 Тест 1: Регистрация водителя ($DRIVER_EMAIL)"
echo "================================================"

# Регистрируем водителя
DRIVER_RESPONSE=$(curl -s -X POST $API_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$DRIVER_EMAIL\",
    \"password\": \"password123\"
  }")

if echo "$DRIVER_RESPONSE" | grep -q "access_token"; then
    DRIVER_TOKEN=$(extract_token "$DRIVER_RESPONSE")
    echo "✅ Водитель зарегистрирован"
else
    echo "❌ Ошибка регистрации водителя: $DRIVER_RESPONSE"
    exit 1
fi

echo ""
echo "🚗 Тест 2: Водитель выходит на линию"
echo "===================================="

# Водитель выходит на линию
echo "🟢 Водитель выходит на линию в точке (10, 10)..."
PRESENCE_RESPONSE=$(curl -s -w "%{http_code}" -X PUT $API_URL/api/v1/drivers/me/presence \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "online",
    "location": {
      "x": 10,
      "y": 10
    }
  }')

if [[ "$PRESENCE_RESPONSE" == "204" ]]; then
    echo "✅ Водитель успешно вышел на линию"
else
    echo "❌ Ошибка при выходе на линию: $PRESENCE_RESPONSE"
    exit 1
fi

echo ""
echo "👥 Тест 3: Регистрация пассажира ($PASSENGER_EMAIL)"
echo "================================"

# Регистрируем пассажира
PASSENGER_RESPONSE=$(curl -s -X POST $API_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$PASSENGER_EMAIL\",
    \"password\": \"password123\"
  }")

if echo "$PASSENGER_RESPONSE" | grep -q "access_token"; then
    PASSENGER_TOKEN=$(extract_token "$PASSENGER_RESPONSE")
    echo "✅ Пассажир зарегистрирован"
else
    echo "❌ Ошибка регистрации пассажира: $PASSENGER_RESPONSE"
    exit 1
fi

echo ""
echo "🎯 Тест 4: Создание заказа"
echo "=========================="

# Пассажир создает заказ
echo "📱 Пассажир создает заказ от (8, 8) до (15, 15)..."
RIDE_RESPONSE=$(curl -s -X POST $API_URL/api/v1/rides \
  -H "Authorization: Bearer $PASSENGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_x": 8,
    "start_y": 8,
    "end_x": 15,
    "end_y": 15
  }')

if echo "$RIDE_RESPONSE" | grep -q "ride_id"; then
    RIDE_ID=$(extract_ride_id "$RIDE_RESPONSE")
    echo "✅ Заказ создан с ID: $RIDE_ID"
else
    echo "❌ Ошибка создания заказа: $RIDE_RESPONSE"
    exit 1
fi

echo ""
echo "⏳ Ожидание работы Matching Service..."
echo "====================================="
echo "⚠️  Убедитесь, что во втором окне запущен: docker-compose exec api python src/run_matching_service.py"
echo "⏱️  Ждем 5 секунд..."

sleep 5

echo ""
echo "✋ Тест 5: Водитель принимает заказ"
echo "=================================="

# Водитель принимает заказ
echo "🤝 Водитель принимает заказ $RIDE_ID..."
ACCEPT_RESPONSE=$(curl -s -w "%{http_code}" -X POST $API_URL/api/v1/rides/$RIDE_ID/accept \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json")

# 200 OK или уже обновленный статус
if [[ "$ACCEPT_RESPONSE" == *"200"* ]]; then
    echo "✅ Заказ успешно принят водителем!"
else
    echo "⚠️  Ответ сервера: $ACCEPT_RESPONSE"
    echo "💡 Если код 200 - все ок. Если ошибка - возможно Matching Service не успел заблокировать водителя."
fi

echo ""
echo "🎉 Тест завершен (ID: $SUFFIX)"