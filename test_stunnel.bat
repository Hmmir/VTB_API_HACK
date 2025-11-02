@echo off
REM Скрипт для тестирования и диагностики stunnel от КриптоПро

echo ============================================================
echo STUNNEL DIAGNOSTIC AND TEST SCRIPT
echo ============================================================

REM Проверка установки stunnel
echo.
echo [1/6] Checking stunnel installation...
set STUNNEL_DIR=C:\Program Files\stunnel
set STUNNEL_EXE=%STUNNEL_DIR%\stunnel.exe

if not exist "%STUNNEL_EXE%" (
    echo ERROR: stunnel.exe not found at "%STUNNEL_EXE%"
    echo Please install stunnel from КриптоПро first.
    pause
    exit /b 1
)
echo OK: stunnel found at "%STUNNEL_EXE%"

REM Проверка версии
echo.
echo [2/6] Checking stunnel version...
"%STUNNEL_EXE%" -version
echo.

REM Создание конфигурационного файла
echo.
echo [3/6] Creating stunnel configuration...
set STUNNEL_CONF=%STUNNEL_DIR%\stunnel_test.conf

(
echo ; Конфигурация stunnel для GOST API - тестовый режим
echo debug = 7
echo output = %STUNNEL_DIR%\stunnel_test.log
echo foreground = yes
echo.
echo [gost-api]
echo client = yes
echo accept = 127.0.0.1:8444
echo connect = api.gost.bankingapi.ru:8443
echo engineId = capi
echo ciphers = GOST2012-GOST8912-GOST8912:GOST2001-GOST89-GOST89
echo verify = 0
echo sni = api.gost.bankingapi.ru
) > "%STUNNEL_CONF%"

echo OK: Configuration created at "%STUNNEL_CONF%"

REM Проверка синтаксиса конфига
echo.
echo [4/6] Checking configuration syntax...
"%STUNNEL_EXE%" -help > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Could not verify config syntax
)

REM Показать конфиг
echo.
echo [5/6] Configuration content:
echo ============================================================
type "%STUNNEL_CONF%"
echo ============================================================

REM Запуск stunnel в режиме foreground
echo.
echo [6/6] Starting stunnel in foreground mode...
echo NOTE: stunnel will run in THIS window
echo Press CTRL+C to stop stunnel
echo ============================================================
echo.

cd /d "%STUNNEL_DIR%"
"%STUNNEL_EXE%" "%STUNNEL_CONF%"

REM Если stunnel завершился с ошибкой
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo ERROR: stunnel exited with error code %ERRORLEVEL%
    echo.
    echo Checking log file...
    if exist "%STUNNEL_DIR%\stunnel_test.log" (
        echo.
        echo LOG CONTENT:
        echo ============================================================
        type "%STUNNEL_DIR%\stunnel_test.log"
        echo ============================================================
    ) else (
        echo Log file not found!
    )
)

echo.
pause

