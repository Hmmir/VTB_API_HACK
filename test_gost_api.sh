#!/bin/bash
# GOST API Connection Test Script
# Требования: OpenSSL с GOST, curl с GOST, сертификат КриптоПРО

TEAM_ID="team075"
TEAM_SECRET="1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
AUTH_URL="https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"
GOST_API_BASE="https://api.gost.bankingapi.ru:8443"

echo "============================================================"
echo "GOST API CONNECTION TEST"
echo "============================================================"

# Step 1: Get access token
echo ""
echo "[1/3] Getting access token..."
TOKEN_RESPONSE=$(curl -s --data "grant_type=client_credentials&client_id=$TEAM_ID&client_secret=$TEAM_SECRET" $AUTH_URL)
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token"
    exit 1
fi

echo "✅ Access token получен: ${ACCESS_TOKEN:0:50}..."

# Step 2: Test GOST API connection
echo ""
echo "[2/3] Testing GOST API connection..."
echo "URL: $GOST_API_BASE/"

# Вариант A: С curl и GOST cipher suites
curl -v \
  --ciphers 'GOST2012-GOST8912-GOST8912:GOST2001-GOST89-GOST89' \
  --cert /path/to/certificate.pem \
  --key /path/to/private.key \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$GOST_API_BASE/" 2>&1

# Вариант B: С OpenSSL s_client
echo ""
echo "[3/3] Alternative: Using OpenSSL s_client..."
echo "GET / HTTP/1.1
Host: api.gost.bankingapi.ru:8443
Authorization: Bearer $ACCESS_TOKEN

" | openssl s_client \
  -connect api.gost.bankingapi.ru:8443 \
  -cipher 'GOST2012-GOST8912-GOST8912' \
  -cert /path/to/certificate.pem \
  -key /path/to/private.key \
  -quiet

echo ""
echo "============================================================"
echo "TEST COMPLETE"
echo "============================================================"
echo ""
echo "Для успешного подключения требуется:"
echo "1. ✅ OpenSSL с GOST - УСТАНОВЛЕН (C:\OpenSSL-GOST\)"
echo "2. ✅ GOST engine - СКОМПИЛИРОВАН"
echo "3. ✅ КриптоПРО CSP - УСТАНОВЛЕН"
echo "4. ⚠️  ГОСТ сертификат - ТРЕБУЕТСЯ (получить на cryptopro.ru)"
echo ""
echo "После получения сертификата замените:"
echo "  /path/to/certificate.pem -> путь к вашему сертификату"
echo "  /path/to/private.key -> путь к приватному ключу"
echo ""

