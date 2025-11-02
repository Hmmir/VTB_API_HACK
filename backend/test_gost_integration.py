"""
Тест интеграции GOST адаптера
Демонстрирует работу с GOST и fallback на стандартный API
"""

import asyncio
import os
from dotenv import load_dotenv
from app.services.gost_adapter import GOSTAdapter, GOSTMode

# Загружаем переменные окружения
load_dotenv()


async def test_gost_adapter():
    """Тестирование GOST адаптера"""
    
    print("=" * 80)
    print("🔒 GOST Adapter Integration Test")
    print("=" * 80)
    print()
    
    # Получаем credentials
    client_id = os.getenv("VTB_CLIENT_ID", "team075")
    client_secret = os.getenv("VTB_CLIENT_SECRET")
    
    if not client_secret:
        print("❌ ERROR: VTB_CLIENT_SECRET not found in environment")
        print("   Please set it in .env file")
        return
    
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {'*' * len(client_secret)}")
    print()
    
    # Test 1: AUTO mode (автоматический выбор)
    print("=" * 80)
    print("Test 1: AUTO Mode (автоматический выбор GOST или стандартный API)")
    print("=" * 80)
    
    adapter_auto = GOSTAdapter(
        client_id=client_id,
        client_secret=client_secret,
        mode=GOSTMode.AUTO
    )
    
    try:
        # Проверяем статус
        status = adapter_auto.get_status()
        print(f"\n📊 Status:")
        print(f"  Mode: {status['gost_mode']}")
        print(f"  GOST Available: {status['gost_available']}")
        print(f"  API Endpoint: {status['current_api']}")
        print(f"  Has Token: {status['has_token']}")
        
        # Получаем токен
        print(f"\n🔑 Getting access token...")
        token = await adapter_auto.get_access_token()
        print(f"  ✅ Token obtained: {token[:20]}...")
        
        # Пробуем выполнить запрос
        print(f"\n📡 Testing API request...")
        try:
            # Пример: получение информации о команде
            result = await adapter_auto.get("/api/v1/team/info")
            print(f"  ✅ API request successful")
            print(f"  Response: {result}")
        except Exception as e:
            print(f"  ⚠️  API request failed (expected if endpoint doesn't exist): {e}")
        
    finally:
        await adapter_auto.close()
    
    print()
    
    # Test 2: GOST mode (принудительно через GOST)
    print("=" * 80)
    print("Test 2: GOST Mode (принудительно через GOST-шлюз)")
    print("=" * 80)
    
    adapter_gost = GOSTAdapter(
        client_id=client_id,
        client_secret=client_secret,
        mode=GOSTMode.GOST
    )
    
    try:
        status = adapter_gost.get_status()
        print(f"\n📊 Status:")
        print(f"  Mode: {status['gost_mode']}")
        print(f"  API Endpoint: {status['current_api']}")
        
        print(f"\n🔑 Getting access token (через GOST)...")
        try:
            token = await adapter_gost.get_access_token()
            print(f"  ✅ Token obtained через GOST-шлюз: {token[:20]}...")
        except Exception as e:
            print(f"  ❌ Failed to get token через GOST: {e}")
            print(f"  💡 Это ожидаемо если GOST-инфраструктура не настроена")
        
    finally:
        await adapter_gost.close()
    
    print()
    
    # Test 3: STANDARD mode (принудительно стандартный API)
    print("=" * 80)
    print("Test 3: STANDARD Mode (принудительно стандартный API)")
    print("=" * 80)
    
    adapter_standard = GOSTAdapter(
        client_id=client_id,
        client_secret=client_secret,
        mode=GOSTMode.STANDARD
    )
    
    try:
        status = adapter_standard.get_status()
        print(f"\n📊 Status:")
        print(f"  Mode: {status['gost_mode']}")
        print(f"  API Endpoint: {status['current_api']}")
        
        print(f"\n🔑 Getting access token (стандартный API)...")
        token = await adapter_standard.get_access_token()
        print(f"  ✅ Token obtained: {token[:20]}...")
        
    finally:
        await adapter_standard.close()
    
    print()
    print("=" * 80)
    print("✅ Tests completed!")
    print("=" * 80)
    print()
    
    # Выводы
    print("📋 Summary:")
    print()
    print("1. AUTO mode:")
    print("   - Автоматически выбирает GOST если доступен")
    print("   - Fallback на стандартный API если GOST недоступен")
    print("   - ✅ Рекомендуется для production")
    print()
    print("2. GOST mode:")
    print("   - Принудительно использует GOST-шлюз")
    print("   - Требует настройки GOST-инфраструктуры")
    print("   - ⚠️  Будет ошибка если GOST не настроен")
    print()
    print("3. STANDARD mode:")
    print("   - Всегда использует стандартный API")
    print("   - Не требует GOST-инфраструктуры")
    print("   - ✅ Подходит для разработки и тестирования")
    print()
    
    # Инструкции для настройки GOST
    print("=" * 80)
    print("📚 Настройка GOST (для корпоративных клиентов)")
    print("=" * 80)
    print()
    print("Для включения GOST-режима выполните:")
    print()
    print("1. Установите КриптоПРО CSP 5.0:")
    print("   https://cryptopro.ru/products/csp/downloads")
    print()
    print("2. Получите тестовый сертификат:")
    print("   https://www.cryptopro.ru/certsrv/certrqma.asp")
    print()
    print("3. Установите OpenSSL с GOST:")
    print("   git clone https://github.com/gost-engine/engine")
    print("   # Следуйте инструкциям в README")
    print()
    print("4. Скомпилируйте curl с GOST OpenSSL:")
    print("   # См. docs/GOST_SETUP_GUIDE.md")
    print()
    print("📖 Полная документация: GOST_CLIENT_READY_SOLUTION.md")
    print()


if __name__ == "__main__":
    asyncio.run(test_gost_adapter())

