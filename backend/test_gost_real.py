"""
Тест реального подключения к GOST API
"""
import os
import sys
import subprocess
import json

sys.path.insert(0, '/app')

from app.integrations.gost_client import GOSTClient


def check_curl():
    """Проверяет наличие curl с GOST поддержкой"""
    print("=" * 60)
    print("ПРОВЕРКА CURL")
    print("=" * 60)
    
    curl_paths = [
        "curl",
        r"C:\Windows\System32\curl.exe",
        r"C:\curl-GOST\bin\curl.exe",
    ]
    
    for path in curl_paths:
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Найден curl: {path}")
                print(f"Версия:\n{result.stdout[:200]}")
                
                # Проверяем поддержку GOST
                if "gost" in result.stdout.lower():
                    print("✅ GOST поддержка обнаружена!")
                else:
                    print("⚠️  GOST поддержка не обнаружена (может работать)")
                
                return path
        except Exception as e:
            continue
    
    print("❌ curl не найден")
    return None


def check_certificate():
    """Проверяет наличие сертификата"""
    print("\n" + "=" * 60)
    print("ПРОВЕРКА СЕРТИФИКАТА")
    print("=" * 60)
    
    container = "VTB_Test_Container"
    
    # Проверяем через csptest
    csptest_path = r"C:\Program Files\Crypto Pro\CSP\csptest.exe"
    
    if os.path.exists(csptest_path):
        try:
            result = subprocess.run(
                [csptest_path, "-keyset", "-enum_cont", "-fqcn", "-verifycontext"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if container in result.stdout:
                print(f"✅ Контейнер {container} найден")
                return True
            else:
                print(f"⚠️  Контейнер {container} не найден в списке")
                print("Вывод csptest:")
                print(result.stdout[:500])
        except Exception as e:
            print(f"❌ Ошибка проверки: {e}")
    else:
        print("⚠️  csptest.exe не найден")
    
    return False


def test_gost_api():
    """Тестирует подключение к GOST API"""
    print("\n" + "=" * 60)
    print("ТЕСТ GOST API")
    print("=" * 60)
    
    team_id = os.getenv("VTB_TEAM_ID", "team075")
    team_secret = os.getenv("VTB_TEAM_SECRET", "1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di")
    
    try:
        client = GOSTClient(team_id, team_secret)
        
        print("\n1. Получение access_token...")
        token = client.get_access_token()
        print(f"✅ Токен получен: {token[:50]}...")
        
        print("\n2. Тестовый запрос к GOST API...")
        # Простой endpoint для теста
        try:
            response = client.request("/api/rb/rewardsPay/hackathon/v1/cards")
            print(f"✅ Запрос успешен!")
            print(f"Ответ: {json.dumps(response, indent=2, ensure_ascii=False)[:500]}")
        except Exception as e:
            print(f"⚠️  Ошибка запроса: {e}")
            print("Это нормально, если endpoint требует конкретных параметров")
        
    except Exception as e:
        print(f"❌ Ошибка: {type(e).__name__}: {str(e)}")
        return False
    
    return True


def main():
    """Главная функция"""
    print("\n" + "=" * 60)
    print("  ПРОВЕРКА GOST ПОДКЛЮЧЕНИЯ")
    print("=" * 60)
    
    # Проверки
    curl_path = check_curl()
    cert_ok = check_certificate()
    
    if not curl_path:
        print("\n❌ curl не найден. Установите curl с GOST поддержкой.")
        print("См. QUICK_GOST_SETUP.md")
        return
    
    if not cert_ok:
        print("\n⚠️  Сертификат не найден. Получите тестовый сертификат.")
        print("См. QUICK_GOST_SETUP.md, Шаг 1")
    
    # Тест API
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ")
    print("=" * 60)
    
    if curl_path and cert_ok:
        test_gost_api()
    else:
        print("\n⚠️  Пропущен тест API из-за отсутствующих компонентов")
    
    print("\n" + "=" * 60)
    print("ИТОГ")
    print("=" * 60)
    print(f"curl: {'✅' if curl_path else '❌'}")
    print(f"Сертификат: {'✅' if cert_ok else '❌'}")
    
    if curl_path and cert_ok:
        print("\n✅ Все компоненты готовы! Можно тестировать GOST API.")
    else:
        print("\n⚠️  Установите недостающие компоненты (см. QUICK_GOST_SETUP.md)")


if __name__ == "__main__":
    main()

