import os
import subprocess
import sys

# Настройка для использования нашего OpenSSL
os.environ['OPENSSL_CONF'] = r'C:\OpenSSL-GOST\ssl\openssl_gost.cnf'
os.environ['OPENSSL_MODULES'] = r'C:\OpenSSL-GOST\lib\ossl-modules'
os.environ['PATH'] = rf'C:\OpenSSL-GOST\bin;{os.environ["PATH"]}'

print("=" * 60)
print("REAL GOST API CONNECTION - METHOD 2")
print("=" * 60)

# Получение токена
import httpx
auth_url = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"
auth_data = {
    "grant_type": "client_credentials",
    "client_id": "team075",
    "client_secret": "1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
}
response = httpx.post(auth_url, data=auth_data, verify=False, timeout=10)
access_token = response.json()["access_token"]
print(f"✅ Access token: {access_token[:50]}...\n")

# Используем curl через subprocess с правильными параметрами
print("[1/1] Testing GOST API with curl + OpenSSL GOST...")

gost_url = "https://api.gost.bankingapi.ru:8443/"
curl_path = r"C:\msys64\mingw64\bin\curl.exe"
openssl_path = r"C:\OpenSSL-GOST\bin\openssl.exe"

# Создаем HTTP запрос
headers = f"Authorization: Bearer {access_token}"

# Пробуем использовать OpenSSL для создания TLS соединения, затем curl для HTTP
try:
    # Используем openssl s_client для установки TLS соединения
    print(f"Connecting to {gost_url}...")
    
    # Создаем HTTP запрос
    http_req = f"GET / HTTP/1.1\r\nHost: api.gost.bankingapi.ru:8443\r\nAuthorization: Bearer {access_token}\r\nConnection: close\r\n\r\n"
    
    # Пробуем через openssl s_client
    process = subprocess.Popen(
        [
            openssl_path,
            "s_client",
            "-connect", "api.gost.bankingapi.ru:8443",
            "-servername", "api.gost.bankingapi.ru",
            "-quiet"
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy()
    )
    
    stdout, stderr = process.communicate(input=http_req, timeout=15)
    
    print("Response:")
    print(stdout[-500:] if len(stdout) > 500 else stdout)
    
    if stderr:
        print("\nErrors:")
        print(stderr[-300:] if len(stderr) > 300 else stderr)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("NOTE: Для полного подключения требуется curl скомпилированный")
print("с OpenSSL GOST или использование готового OpenSSL с GOST")
print("=" * 60)

