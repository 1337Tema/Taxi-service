#!/usr/bin/env python3
"""
Простой скрипт для проверки доступности всех API эндпоинтов
"""
import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"


async def test_endpoints():
    """Проверяет доступность всех основных эндпоинтов"""
    async with httpx.AsyncClient(trust_env=False) as client:
        print("🔍 Проверка доступности API эндпоинтов...")
        print("=" * 50)
        
        # Список эндпоинтов для проверки
        endpoints = [
            ("GET", "/healthcheck", "Проверка здоровья"),
            ("GET", "/docs", "Swagger документация"),
            ("POST", "/api/v1/auth/register", "Регистрация"),
            ("POST", "/api/v1/auth/login", "Логин"),
            ("PUT", "/api/v1/drivers/me/presence", "Статус водителя"),
            ("POST", "/api/v1/rides", "Создание поездки"),
            ("GET", "/api/v1/rides/history", "История поездок"),
        ]
        
        for method, path, description in endpoints:
            try:
                if method == "GET":
                    response = await client.get(f"{BASE_URL}{path}")
                else:
                    # Для POST/PUT отправляем пустой JSON
                    response = await client.request(
                        method, 
                        f"{BASE_URL}{path}",
                        json={}
                    )
                
                # Проверяем, что эндпоинт существует (не 404)
                if response.status_code == 404:
                    print(f"❌ {method} {path} - {description}: NOT FOUND")
                elif response.status_code in [401, 422]:
                    # 401 - нет авторизации, 422 - неверные данные (это нормально)
                    print(f"✅ {method} {path} - {description}: OK (требует данные/авторизацию)")
                elif response.status_code < 500:
                    print(f"✅ {method} {path} - {description}: OK")
                else:
                    print(f"⚠️  {method} {path} - {description}: SERVER ERROR ({response.status_code})")
                    
            except Exception as e:
                print(f"❌ {method} {path} - {description}: ERROR - {e}")
        
        print("\n" + "=" * 50)
        print("✅ Проверка завершена!")


if __name__ == "__main__":
    asyncio.run(test_endpoints())