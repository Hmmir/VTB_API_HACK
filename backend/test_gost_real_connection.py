import os
import sys
import socket
import ssl
import subprocess

# Настройка OpenSSL
os.environ['OPENSSL_CONF'] = r'C:\OpenSSL-GOST\ssl\openssl.cnf'
os.environ['OPENSSL_MODULES'] = r'C:\OpenSSL-GOST\lib\ossl-modules'
os.environ['PATH'] = rf'C:\OpenSSL-GOST\bin;{os.environ["PATH"]}'

print("=" * 60)
print("REAL GOST API CONNECTION")
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

# Создание HTTP запроса через OpenSSL s_client
gost_api = "api.gost.bankingapi.ru"
gost_port = 8443

http_request = f"""GET / HTTP/1.1
Host: {gost_api}:{gost_port}
Authorization: Bearer {access_token}
Connection: close

"""

print(f"[1/2] Connecting to {gost_api}:{gost_port}...")
print("[2/2] Using OpenSSL s_client with GOST...")

try:
    openssl_path = r"C:\OpenSSL-GOST\bin\openssl.exe"
    
    # Используем s_client для подключения
    process = subprocess.Popen(
        [
            openssl_path,
            "s_client",
            "-connect", f"{gost_api}:{gost_port}",
            "-servername", gost_api,
            "-engine", "capi",  # Используем КриптоПРО engine
            "-key", r"\\.\HDIMAGE\VTB_Test_Container",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy()
    )
    
    stdout, stderr = process.communicate(input=http_request, timeout=10)
    
    print("STDOUT:")
    print(stdout[:1000])
    
    if stderr:
        print("\nSTDERR:")
        print(stderr[:500])
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

