"""
Скрипт для тестирования JWT аутентификации.
"""
import asyncio
import httpx
import uuid  

# Используем 127.0.0.1 чтобы не зависеть от глюков Windows/Nginx
BASE_URL = "http://127.0.0.1:8000/api/v1"


async def test_authentication():
    """Тестирует полный цикл аутентификации."""
    # trust_env=False отключает прокси Windows
    async with httpx.AsyncClient(trust_env=False) as client:
        print("=== Тест аутентификации ===")

        # Генерируем уникальный email для каждого теста
        random_suffix = uuid.uuid4().hex[:8]
        test_email = f"test_{random_suffix}@example.com"
        print(f"📧 Используем email: {test_email}")

        # 1. Регистрация нового пользователя
        print("\n1. Регистрация пользователя...")
        register_data = {
            "email": test_email,
            "password": "testpassword123"
        }

        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
            if response.status_code == 201:
                token_data = response.json()
                access_token = token_data["access_token"]
                print(f"✅ Регистрация успешна. Токен получен.")
            else:
                print(f"❌ Ошибка регистрации: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Ошибка при регистрации: {e}")
            return

        # 2. Логин с теми же данными
        print("\n2. Логин пользователя...")
        login_data = {
            "email": test_email,
            "password": "testpassword123"
        }

        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                print(f"✅ Логин успешен.")
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

        # 4. Тест без токена (ожидается 401 или 403)
        print("\n4. Тест без токена (ожидается 401/403)...")
        try:
            response = await client.put(f"{BASE_URL}/drivers/me/presence", json=presence_data)
            if response.status_code in [401, 403]:
                print(f"✅ Защита работает: запрос без токена отклонен ({response.status_code})")
            else:
                print(f"❌ Защита не работает: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Ошибка при тесте без токена: {e}")

        # 5. Тест с неверным токеном (должен вернуть 401 или 403)
        print("\n5. Тест с неверным токеном (ожидается 401/403)...")
        bad_headers = {"Authorization": "Bearer invalid_token_here"}
        try:
            response = await client.put(
                f"{BASE_URL}/drivers/me/presence",
                json=presence_data,
                headers=bad_headers
            )
            if response.status_code in [401, 403]:
                print(f"✅ Защита работает: запрос с неверным токеном отклонен ({response.status_code})")
            else:
                print(f"❌ Защита не работает: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Ошибка при тесте с неверным токеном: {e}")


if __name__ == "__main__":
    asyncio.run(test_authentication())