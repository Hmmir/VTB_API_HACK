import os
import sys
import subprocess
import json

# Настройка OpenSSL
os.environ['OPENSSL_CONF'] = r'C:\OpenSSL-GOST\ssl\openssl_gost.cnf'
os.environ['OPENSSL_MODULES'] = r'C:\OpenSSL-GOST\lib\ossl-modules'
os.environ['PATH'] = rf'C:\OpenSSL-GOST\bin;{os.environ["PATH"]}'

print("=" * 70)
print("REAL GOST API CONNECTION - FINAL ATTEMPT")
print("=" * 70)

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

# Тестируем несколько методов подключения
gost_api = "api.gost.bankingapi.ru"
gost_port = 8443

methods = [
    {
        "name": "OpenSSL s_client with CAPI engine",
        "cmd": [
            r"C:\OpenSSL-GOST\bin\openssl.exe",
            "s_client",
            "-connect", f"{gost_api}:{gost_port}",
            "-servername", gost_api,
            "-engine", "capi"
        ]
    },
    {
        "name": "OpenSSL s_client with GOST engine",
        "cmd": [
            r"C:\OpenSSL-GOST\bin\openssl.exe",
            "s_client",
            "-connect", f"{gost_api}:{gost_port}",
            "-servername", gost_api,
            "-engine", "gost"
        ]
    }
]

http_request = f"GET / HTTP/1.1\r\nHost: {gost_api}:{gost_port}\r\nAuthorization: Bearer {access_token}\r\nConnection: close\r\n\r\n"

for method in methods:
    print(f"\n{'='*70}")
    print(f"Method: {method['name']}")
    print(f"{'='*70}")
    
    try:
        process = subprocess.Popen(
            method['cmd'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )
        
        stdout, stderr = process.communicate(input=http_request, timeout=15)
        
        # Ищем успешный ответ
        if "HTTP/" in stdout or "200" in stdout or "accounts" in stdout.lower():
            print("✅ SUCCESS! Got response:")
            print("-" * 70)
            # Выводим последние строки с HTTP ответом
            lines = stdout.split('\n')
            http_start = None
            for i, line in enumerate(lines):
                if line.startswith('HTTP/') or 'accounts' in line.lower():
                    http_start = max(0, i - 2)
                    break
            
            if http_start is not None:
                print('\n'.join(lines[http_start:http_start+20]))
            else:
                print(stdout[-500:])
            print("-" * 70)
            break
        
        # Показываем ключевые моменты
        if "CONNECTED" in stdout:
            print("✅ TLS connection established!")
        if "Cipher" in stdout:
            cipher_line = [l for l in stdout.split('\n') if 'Cipher' in l]
            if cipher_line:
                print(f"   {cipher_line[0].strip()}")
        if "error" in stderr.lower():
            print(f"⚠️  Errors: {stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout")
        process.kill()
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("STATUS: Все методы протестированы")
print("=" * 70)

