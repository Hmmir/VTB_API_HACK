@echo off
REM Простой тест GOST API как требует жюри

set TEAM_ID=team075
set TEAM_SECRET=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di
set AUTH_URL=https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token
set GOST_API=https://api.gost.bankingapi.ru:8443/api/rb/rewardsPay/hackathon/v1/cards/accounts

set CURL=C:\msys64\usr\bin\curl.exe

echo ============================================================
echo GOST API TEST (JURY REQUIREMENTS)
echo ============================================================
echo.
echo УСЛОВИЯ ЖЮРИ:
echo 1. OpenSSL с GOST: C:\OpenSSL-GOST-Shared\bin\openssl.exe
echo 2. curl с GOST: %CURL%
echo 3. Сертификат: VTB_Test_Container
echo.
echo ============================================================

REM Шаг 1: Получить access token
echo.
echo [1/2] Getting access token...
echo.

%CURL% -v -X POST "%AUTH_URL%" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "grant_type=client_credentials&client_id=%TEAM_ID%&client_secret=%TEAM_SECRET%" ^
  -o token_response.json

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to get token
    pause
    exit /b 1
)

echo.
echo Token response:
type token_response.json
echo.

REM Извлечь access token
for /f "tokens=2 delims=:," %%a in ('findstr /C:"access_token" token_response.json') do (
    set "TOKEN=%%a"
)
REM Убрать кавычки
set TOKEN=%TOKEN:"=%
set TOKEN=%TOKEN: =%

echo Access token: %TOKEN:~0,30%...
echo.

REM Шаг 2: Вызвать GOST API
echo [2/2] Calling GOST API...
echo URL: %GOST_API%
echo.

%CURL% -v -X GET "%GOST_API%" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -k

echo.
echo ============================================================
echo TEST COMPLETE
echo ============================================================

del token_response.json 2>nul

pause

