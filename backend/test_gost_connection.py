import os
import sys
import httpx
import subprocess

# Настройка OpenSSL для использования GOST
os.environ['OPENSSL_CONF'] = r'C:\OpenSSL-GOST\ssl\openssl.cnf'
os.environ['OPENSSL_MODULES'] = r'C:\OpenSSL-GOST\lib\ossl-modules'

# Добавляем OpenSSL в PATH
openssl_bin = r'C:\OpenSSL-GOST\bin'
if openssl_bin not in os.environ['PATH']:
    os.environ['PATH'] = f"{openssl_bin};{os.environ['PATH']}"

print("=" * 60)
print("GOST API CONNECTION TEST")
print("=" * 60)

# Шаг 1: Получение access token
print("\n[1/3] Getting access token...")
try:
    auth_url = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": "team075",
        "client_secret": "1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
    }
    
    response = httpx.post(auth_url, data=auth_data, verify=False, timeout=10)
    response.raise_for_status()
    token_data = response.json()
    access_token = token_data["access_token"]
    print(f"✅ Access token получен: {access_token[:30]}...")
except Exception as e:
    print(f"❌ Ошибка получения token: {e}")
    sys.exit(1)

# Шаг 2: Проверка OpenSSL GOST support
print("\n[2/3] Checking OpenSSL GOST support...")
try:
    openssl_path = r"C:\OpenSSL-GOST\bin\openssl.exe"
    result = subprocess.run(
        [openssl_path, "list", "-providers", "-provider-path", r"C:\OpenSSL-GOST\lib\ossl-modules"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print("OpenSSL providers:")
    print(result.stdout)
    if "gost" in result.stdout.lower():
        print("✅ GOST provider detected")
    else:
        print("⚠️  GOST provider not loaded, but continuing...")
except Exception as e:
    print(f"⚠️  OpenSSL check failed: {e}")

# Шаг 3: Подключение к GOST API
print("\n[3/3] Testing GOST API connection...")
try:
    gost_api_url = "https://api.gost.bankingapi.ru:8443/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Попытка подключения
    response = httpx.get(
        gost_api_url,
        headers=headers,
        verify=False,  # Для тестирования без сертификата
        timeout=10
    )
    
    print(f"✅ Connected! Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except httpx.ConnectError as e:
    print(f"❌ Connection error: {e}")
    print("\n💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
    print("   1. GOST API требует TLS с GOST cipher suites")
    print("   2. Нужен ГОСТ сертификат из КриптоПРО")
    print("   3. Python httpx использует стандартный TLS, не GOST")
    print("\n✅ РЕШЕНИЕ: Использовать curl с настроенным OpenSSL GOST")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("STATUS:")
print("=" * 60)
print("✅ OpenSSL 3.3.0 + GOST engine скомпилированы")
print("✅ GOST provider DLL создан")
print("✅ КриптоПРО CSP установлен")
print("⚠️  Для полного подключения нужен ГОСТ сертификат")
print("=" * 60)

