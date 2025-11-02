@echo off
REM Скрипт для просмотра логов stunnel

echo ============================================================
echo STUNNEL LOGS VIEWER
echo ============================================================

set STUNNEL_DIR=C:\Program Files\stunnel

echo.
echo Checking for log files in: %STUNNEL_DIR%
echo.

REM Проверка stunnel_test.log
if exist "%STUNNEL_DIR%\stunnel_test.log" (
    echo ============================================================
    echo FILE: stunnel_test.log
    echo ============================================================
    type "%STUNNEL_DIR%\stunnel_test.log"
    echo.
) else (
    echo stunnel_test.log not found
)

REM Проверка stunnel.log
if exist "%STUNNEL_DIR%\stunnel.log" (
    echo ============================================================
    echo FILE: stunnel.log
    echo ============================================================
    type "%STUNNEL_DIR%\stunnel.log"
    echo.
) else (
    echo stunnel.log not found
)

REM Проверка других логов
echo.
echo Other files in stunnel directory:
dir /b "%STUNNEL_DIR%\*.log" 2>nul

echo.
echo ============================================================
pause

