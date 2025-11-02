@echo off
REM REAL GOST API CONNECTION SCRIPT
REM Использует наш OpenSSL с GOST и КриптоПРО сертификат

setlocal

set TEAM_ID=team075
set TEAM_SECRET=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di
set AUTH_URL=https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token
set GOST_API=https://api.gost.bankingapi.ru:8443

echo ============================================================
echo REAL GOST API CONNECTION TEST
echo ============================================================
echo.

echo [1/3] Getting access token...
powershell -Command "$response = Invoke-WebRequest -Uri '%AUTH_URL%' -Method POST -Body @{grant_type='client_credentials'; client_id='%TEAM_ID%'; client_secret='%TEAM_SECRET%'} -UseBasicParsing; $token = ($response.Content | ConvertFrom-Json).access_token; $env:ACCESS_TOKEN = $token; [System.Environment]::SetEnvironmentVariable('ACCESS_TOKEN', $token, 'Process'); Write-Host 'Token:' $token.Substring(0,50)'...'"

set ACCESS_TOKEN=%ACCESS_TOKEN%
if "%ACCESS_TOKEN%"=="" (
    echo ERROR: Failed to get access token
    exit /b 1
)

echo.
echo [2/3] Testing GOST API connection...
echo URL: %GOST_API%/
echo.

REM Настройка OpenSSL
set OPENSSL_CONF=C:\OpenSSL-GOST\ssl\openssl_gost.cnf
set OPENSSL_MODULES=C:\OpenSSL-GOST\lib\ossl-modules
set PATH=C:\OpenSSL-GOST\bin;%PATH%

REM Создаем HTTP запрос
echo GET / HTTP/1.1 > request.txt
echo Host: api.gost.bankingapi.ru:8443 >> request.txt
echo Authorization: Bearer %ACCESS_TOKEN% >> request.txt
echo Connection: close >> request.txt
echo. >> request.txt

echo [3/3] Connecting via OpenSSL s_client...
echo.

REM Пробуем подключиться через OpenSSL с КриптоПРО engine
C:\OpenSSL-GOST\bin\openssl.exe s_client ^
  -connect api.gost.bankingapi.ru:8443 ^
  -servername api.gost.bankingapi.ru ^
  -engine capi ^
  -key \\.\HDIMAGE\VTB_Test_Container ^
  < request.txt

echo.
echo ============================================================
echo CONNECTION ATTEMPTED
echo ============================================================

del request.txt 2>nul

endlocal

