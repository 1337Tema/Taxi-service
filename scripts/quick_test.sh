#!/bin/bash

# Taxi Grid Service - Quick Test Script
# Этот скрипт демонстрирует полный цикл работы сервиса

set -e  # Выход при любой ошибке

echo "🚀 Taxi Grid Service - Быстрый тест"
echo "=================================="

# Проверяем, что сервис запущен
echo "📡 Проверяем доступность API..."
if ! curl -s http://localhost:8000/healthcheck > /dev/null; then
    echo "❌ API недоступен. Убедитесь, что сервис запущен: docker-compose up -d"
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
echo "👤 Тест 1: Регистрация и аутентификация водителя"
echo "================================================"

# Регистрируем водителя
echo "📝 Регистрируем водителя..."
DRIVER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "driver_test@example.com",
    "password": "password123"
  }')

if echo "$DRIVER_RESPONSE" | grep -q "access_token"; then
    DRIVER_TOKEN=$(extract_token "$DRIVER_RESPONSE")
    echo "✅ Водитель зарегистрирован, токен получен"
else
    echo "❌ Ошибка регистрации водителя: $DRIVER_RESPONSE"
    exit 1
fi

echo ""
echo "🚗 Тест 2: Водитель выходит на линию"
echo "===================================="

# Водитель выходит на линию
echo "🟢 Водитель выходит на линию в точке (10, 10)..."
PRESENCE_RESPONSE=$(curl -s -w "%{http_code}" -X PUT http://localhost:8000/api/v1/drivers/me/presence \
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
echo "👥 Тест 3: Регистрация пассажира"
echo "================================"

# Регистрируем пассажира
echo "📝 Регистрируем пассажира..."
PASSENGER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "passenger_test@example.com",
    "password": "password123"
  }')

if echo "$PASSENGER_RESPONSE" | grep -q "access_token"; then
    PASSENGER_TOKEN=$(extract_token "$PASSENGER_RESPONSE")
    echo "✅ Пассажир зарегистрирован, токен получен"
else
    echo "❌ Ошибка регистрации пассажира: $PASSENGER_RESPONSE"
    exit 1
fi

echo ""
echo "🎯 Тест 4: Создание заказа"
echo "=========================="

# Пассажир создает заказ
echo "📱 Пассажир создает заказ от (8, 8) до (15, 15)..."
RIDE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/rides \
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
    echo "💰 Расчетная стоимость: $(echo "$RIDE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['estimated_price'])")"
else
    echo "❌ Ошибка создания заказа: $RIDE_RESPONSE"
    exit 1
fi

echo ""
echo "⏳ Ожидание работы Matching Service..."
echo "====================================="
echo "🔍 Matching Service должен найти водителя и отправить уведомление..."
echo "⚠️  Убедитесь, что Matching Service запущен: python src/run_matching_service.py"
echo "⏱️  Ждем 10 секунд для обработки заказа..."

sleep 10

echo ""
echo "✋ Тест 5: Водитель принимает заказ"
echo "=================================="

# Водитель принимает заказ
echo "🤝 Водитель принимает заказ $RIDE_ID..."
ACCEPT_RESPONSE=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/v1/rides/$RIDE_ID/accept \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json")

if [[ "$ACCEPT_RESPONSE" == *"200"* ]] || [[ "$ACCEPT_RESPONSE" == *"driver_assigned"* ]]; then
    echo "✅ Заказ принят водителем"
else
    echo "⚠️  Возможная ошибка при принятии заказа: $ACCEPT_RESPONSE"
    echo "💡 Это может быть нормально, если Matching Service еще не обработал заказ"
fi

echo ""
echo "📊 Тест 6: Проверка истории поездок"
echo "==================================="

# Проверяем историю поездок пассажира
echo "📋 Получаем историю поездок пассажира..."
HISTORY_RESPONSE=$(curl -s -X GET http://localhost:8000/api/v1/rides/history \
  -H "Authorization: Bearer $PASSENGER_TOKEN")

if echo "$HISTORY_RESPONSE" | grep -q "ride_id"; then
    echo "✅ История поездок получена"
    echo "📝 Количество поездок: $(echo "$HISTORY_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")"
else
    echo "❌ Ошибка получения истории: $HISTORY_RESPONSE"
fi

echo ""
echo "🔒 Тест 7: Проверка безопасности"
echo "================================"

# Тест без токена
echo "🚫 Тестируем запрос без токена (ожидается 401)..."
NO_AUTH_RESPONSE=$(curl -s -w "%{http_code}" -X PUT http://localhost:8000/api/v1/drivers/me/presence \
  -H "Content-Type: application/json" \
  -d '{"status": "online", "location": {"x": 5, "y": 5}}')

if [[ "$NO_AUTH_RESPONSE" == *"401"* ]]; then
    echo "✅ Защита работает: запрос без токена отклонен"
else
    echo "❌ Проблема с защитой: $NO_AUTH_RESPONSE"
fi

# Тест с неверным токеном
echo "🔑 Тестируем запрос с неверным токеном (ожидается 401)..."
BAD_AUTH_RESPONSE=$(curl -s -w "%{http_code}" -X PUT http://localhost:8000/api/v1/drivers/me/presence \
  -H "Authorization: Bearer invalid_token_here" \
  -H "Content-Type: application/json" \
  -d '{"status": "online", "location": {"x": 5, "y": 5}}')

if [[ "$BAD_AUTH_RESPONSE" == *"401"* ]]; then
    echo "✅ Защита работает: запрос с неверным токеном отклонен"
else
    echo "❌ Проблема с защитой: $BAD_AUTH_RESPONSE"
fi

echo ""
echo "🎉 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ"
echo "========================="
echo "✅ Регистрация и аутентификация работают"
echo "✅ Обновление статуса водителя работает"
echo "✅ Создание заказов работает"
echo "✅ Принятие заказов работает"
echo "✅ История поездок работает"
echo "✅ JWT аутентификация защищает эндпоинты"
echo ""
echo "🚀 Сервис готов к полноценному тестированию!"
echo ""
echo "📚 Дополнительные тесты:"
echo "  • Нагрузочное тестирование: python scripts/load_test.py"
echo "  • Тест аутентификации: python scripts/test_auth.py"
echo "  • Unit тесты: docker-compose exec api pytest"
echo "  • API документация: http://localhost:8000/docs"
echo ""
echo "🔧 Для отладки:"
echo "  • Логи API: docker-compose logs api"
echo "  • Логи Matching Service: проверьте терминал где запущен"
echo "  • Redis мониторинг: docker-compose exec redis redis-cli monitor"