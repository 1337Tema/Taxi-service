"""
Скрипт для тестирования JWT аутентификации.
"""
import asyncio
import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_authentication():
    """Тестирует полный цикл аутентификации."""
    async with httpx.AsyncClient() as client:
        print("=== Тест аутентификации ===")
        
        # 1. Регистрация нового пользователя
        print("\n1. Регистрация пользователя...")
        register_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
            if response.status_code == 201:
                token_data = response.json()
                access_token = token_data["access_token"]
                print(f"✅ Регистрация успешна. Токен получен: {access_token[:20]}...")
            else:
                print(f"❌ Ошибка регистрации: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Ошибка при регистрации: {e}")
            return
        
        # 2. Логин с теми же данными
        print("\n2. Логин пользователя...")
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                print(f"✅ Логин успешен. Токен получен: {access_token[:20]}...")
            else:
                print(f"❌ Ошибка логина: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Ошибка при логине: {e}")
            return
        
        # 3. Тест защищенного эндпоинта с токеном
        print("\n3. Тест защищенного эндпоинта...")
        headers = {"Authorization": f"Bearer {access_token}"}
        presence_data = {
            "status": "online",
            "location": {"x": 10, "y": 15}
        }
        
        try:
            response = await client.put(
                f"{BASE_URL}/drivers/me/presence", 
                json=presence_data,
                headers=headers
            )
            if response.status_code == 204:
                print("✅ Защищенный эндпоинт работает с валидным токеном")
            else:
                print(f"❌ Ошибка защищенного эндпоинта: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Ошибка при обращении к защищенному эндпоинту: {e}")
        
        # 4. Тест без токена (должен вернуть 401)
        print("\n4. Тест без токена (ожидается 401)...")
        try:
            response = await client.put(f"{BASE_URL}/drivers/me/presence", json=presence_data)
            if response.status_code == 401:
                print("✅ Защита работает: запрос без токена отклонен")
            else:
                print(f"❌ Защита не работает: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Ошибка при тесте без токена: {e}")
        
        # 5. Тест с неверным токеном (должен вернуть 401)
        print("\n5. Тест с неверным токеном (ожидается 401)...")
        bad_headers = {"Authorization": "Bearer invalid_token_here"}
        try:
            response = await client.put(
                f"{BASE_URL}/drivers/me/presence", 
                json=presence_data,
                headers=bad_headers
            )
            if response.status_code == 401:
                print("✅ Защита работает: запрос с неверным токеном отклонен")
            else:
                print(f"❌ Защита не работает: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Ошибка при тесте с неверным токеном: {e}")

if __name__ == "__main__":
    print("Убедитесь, что сервер запущен на http://127.0.0.1:8000")
    asyncio.run(test_authentication())