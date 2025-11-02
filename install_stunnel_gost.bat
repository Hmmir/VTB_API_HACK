@echo off
REM ============================================================
REM ФИНАЛЬНОЕ РЕШЕНИЕ - УСТАНОВКА STUNNEL С КРИПТОПРО CSP
REM ============================================================

echo.
echo ============================================================
echo   ФИНАЛЬНОЕ РЕШЕНИЕ - STUNNEL С КРИПТОПРО CSP
echo ============================================================
echo.

echo ШАГ 1: Скачайте stunnel
echo ----------------------------------------
echo URL: https://www.stunnel.org/downloads.html
echo Файл: stunnel-5.71-win64-installer.exe (или новее)
echo.
echo Нажмите любую клавишу после скачивания...
pause >nul

echo.
echo ШАГ 2: Установите stunnel
echo ----------------------------------------
echo 1. Запустите установщик
echo 2. Выберите путь установки по умолчанию
echo 3. Завершите установку
echo.
echo Нажмите любую клавишу после установки...
pause >nul

echo.
echo ШАГ 3: Создаем конфигурацию stunnel
echo ----------------------------------------

set STUNNEL_CONF=C:\Program Files (x86)\stunnel\config\gost-api.conf

echo ; GOST API Tunnel Configuration > "%STUNNEL_CONF%"
echo [gost-api] >> "%STUNNEL_CONF%"
echo client = yes >> "%STUNNEL_CONF%"
echo accept = 127.0.0.1:8444 >> "%STUNNEL_CONF%"
echo connect = api.gost.bankingapi.ru:8443 >> "%STUNNEL_CONF%"
echo engineId = capi >> "%STUNNEL_CONF%"
echo engineCtrl = CAPI_CERT_CONTEXT:VTB_Test_Container >> "%STUNNEL_CONF%"

echo ✅ Конфигурация создана: %STUNNEL_CONF%
echo.

echo ШАГ 4: Запускаем stunnel
echo ----------------------------------------
echo Запуск: "C:\Program Files (x86)\stunnel\bin\stunnel.exe" "%STUNNEL_CONF%"
start "GOST API Tunnel" "C:\Program Files (x86)\stunnel\bin\stunnel.exe" "%STUNNEL_CONF%"

echo.
echo ============================================================
echo   STUNNEL ЗАПУЩЕН!
echo ============================================================
echo.
echo Теперь GOST API доступен локально:
echo   http://127.0.0.1:8444/api/rb/rewardsPay/hackathon/v1/cards/accounts
echo.
echo В коде приложения измените URL:
echo   ОТ:  https://api.gost.bankingapi.ru:8443
echo   НА:  http://127.0.0.1:8444
echo.
echo Нажмите любую клавишу для выхода...
pause >nul

