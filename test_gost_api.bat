@echo off
REM GOST API Connection Test Script (Windows)
REM Требования: OpenSSL с GOST, curl с GOST, сертификат КриптоПРО

set TEAM_ID=team075
set TEAM_SECRET=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di
set AUTH_URL=https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token
set GOST_API_BASE=https://api.gost.bankingapi.ru:8443

echo ============================================================
echo GOST API CONNECTION TEST
echo ============================================================
echo.

echo [1/3] Getting access token...
curl -s --data "grant_type=client_credentials&client_id=%TEAM_ID%&client_secret=%TEAM_SECRET%" %AUTH_URL% > token.json
for /f "tokens=2 delims=:" %%a in ('findstr "access_token" token.json') do set ACCESS_TOKEN=%%a
set ACCESS_TOKEN=%ACCESS_TOKEN:"=%
set ACCESS_TOKEN=%ACCESS_TOKEN:,=%
set ACCESS_TOKEN=%ACCESS_TOKEN: =%

echo ✅ Access token получен: %ACCESS_TOKEN:~0,50%...
echo.

echo [2/3] Testing GOST API connection...
echo URL: %GOST_API_BASE%/
echo.

REM Вариант A: С curl и GOST cipher suites (требует curl с GOST)
C:\msys64\mingw64\bin\curl.exe -v ^
  --ciphers "GOST2012-GOST8912-GOST8912:GOST2001-GOST89-GOST89" ^
  --cert "C:\path\to\certificate.pem" ^
  --key "C:\path\to\private.key" ^
  -H "Authorization: Bearer %ACCESS_TOKEN%" ^
  "%GOST_API_BASE%/"

echo.
echo [3/3] Testing with OpenSSL s_client...
echo.

REM Вариант B: С OpenSSL s_client
set OPENSSL_CONF=C:\OpenSSL-GOST\ssl\openssl.cnf
set PATH=C:\OpenSSL-GOST\bin;%PATH%

(
echo GET / HTTP/1.1
echo Host: api.gost.bankingapi.ru:8443
echo Authorization: Bearer %ACCESS_TOKEN%
echo.
) | C:\OpenSSL-GOST\bin\openssl.exe s_client ^
  -connect api.gost.bankingapi.ru:8443 ^
  -cipher "GOST2012-GOST8912-GOST8912" ^
  -cert "C:\path\to\certificate.pem" ^
  -key "C:\path\to\private.key"

echo.
echo ============================================================
echo TEST COMPLETE
echo ============================================================
echo.
echo Для успешного подключения требуется:
echo 1. ✅ OpenSSL с GOST - УСТАНОВЛЕН (C:\OpenSSL-GOST\)
echo 2. ✅ GOST engine - СКОМПИЛИРОВАН
echo 3. ✅ КриптоПРО CSP - УСТАНОВЛЕН
echo 4. ⚠️  ГОСТ сертификат - ТРЕБУЕТСЯ (получить на cryptopro.ru)
echo.
echo После получения сертификата замените:
echo   C:\path\to\certificate.pem -^> путь к вашему сертификату
echo   C:\path\to\private.key -^> путь к приватному ключу
echo.

del token.json

