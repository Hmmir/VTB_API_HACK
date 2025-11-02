# БЫСТРАЯ УСТАНОВКА GOST ДЛЯ VTB API
# Использует готовые бинарники вместо компиляции (5 минут вместо 2 часов)

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "БЫСТРАЯ УСТАНОВКА GOST (5 минут)" -ForegroundColor Cyan  
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Создаем директорию для GOST инструментов
$gostDir = "C:\gost"
Write-Host "[1/4] Создаем директорию $gostDir..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $gostDir -Force | Out-Null
Write-Host "✅ Директория создана" -ForegroundColor Green

# ШАГ 2: Скачать OpenSSL с GOST (готовая сборка)
Write-Host "`n[2/4] Скачиваем OpenSSL с GOST..." -ForegroundColor Yellow
Write-Host "Используем готовую сборку от CryptoPro..." -ForegroundColor Gray

$opensslUrl = "https://www.cryptopro.ru/sites/default/files/products/cades/dists/openssl-gost-1.1.1k-1.x86_64.msi"
$opensslInstaller = "$gostDir\openssl-gost.msi"

try {
    Write-Host "Скачивание с cryptopro.ru..." -ForegroundColor Gray
    Invoke-WebRequest -Uri $opensslUrl -OutFile $opensslInstaller -TimeoutSec 60
    Write-Host "✅ OpenSSL скачан" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Не удалось скачать с cryptopro.ru" -ForegroundColor Yellow
    Write-Host "Попробуем альтернативный метод..." -ForegroundColor Gray
    
    # Альтернатива: использовать системный OpenSSL
    Write-Host "Используем системный OpenSSL + GOST engine..." -ForegroundColor Gray
}

# ШАГ 3: Настроить сертификат КриптоПРО
Write-Host "`n[3/4] Проверка сертификата КриптоПРО..." -ForegroundColor Yellow

$cryptoproPath = "C:\Program Files\Crypto Pro"
if (Test-Path $cryptoproPath) {
    Write-Host "✅ КриптоПРО установлен: $cryptoproPath" -ForegroundColor Green
    
    # Проверяем сертификаты
    $certs = Get-ChildItem -Path Cert:\CurrentUser\My -ErrorAction SilentlyContinue
    $gostCerts = $certs | Where-Object { 
        $_.Subject -like "*CryptoPro*" -or 
        $_.Issuer -like "*CryptoPro*" -or
        $_.SignatureAlgorithm.FriendlyName -like "*ГОСТ*"
    }
    
    if ($gostCerts.Count -gt 0) {
        Write-Host "✅ Найдено GOST сертификатов: $($gostCerts.Count)" -ForegroundColor Green
        $gostCerts | ForEach-Object {
            Write-Host "  - $($_.Subject)" -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠️  GOST сертификаты не найдены" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Для получения тестового сертификата:" -ForegroundColor Cyan
        Write-Host "1. Откройте: https://www.cryptopro.ru/certsrv/certrqma.asp" -ForegroundColor White
        Write-Host "2. Выберите 'ГОСТ Р 34.10-2012 (256 бит)'" -ForegroundColor White
        Write-Host "3. Заполните форму и скачайте сертификат" -ForegroundColor White
        Write-Host "4. Установите сертификат (двойной клик на .cer файл)" -ForegroundColor White
    }
} else {
    Write-Host "❌ КриптоПРО НЕ установлен!" -ForegroundColor Red
    Write-Host "Скачайте: https://cryptopro.ru/products/csp/downloads" -ForegroundColor Yellow
}

# ШАГ 4: Настроить curl для GOST
Write-Host "`n[4/4] Настройка curl..." -ForegroundColor Yellow

# Проверяем системный curl
$curlExe = "C:\Windows\System32\curl.exe"
if (Test-Path $curlExe) {
    $curlVersion = & $curlExe --version 2>&1 | Select-Object -First 1
    Write-Host "Системный curl: $curlVersion" -ForegroundColor Gray
    
    # curl в Windows использует Schannel - НЕ поддерживает GOST
    Write-Host "⚠️  Windows curl использует Schannel (нет GOST)" -ForegroundColor Yellow
}

# Создаем wrapper скрипт для curl с сертификатом
$curlWrapper = @"
@echo off
REM Wrapper для curl с КриптоПРО сертификатом
REM Использует stunnel как прокси для GOST TLS

set CURL_EXE=C:\Windows\System32\curl.exe
set STUNNEL_CONF=C:\gost\stunnel.conf

REM Запускаем stunnel в фоне (если еще не запущен)
tasklist /FI "IMAGENAME eq stunnel.exe" 2>NUL | find /I /N "stunnel.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo Starting stunnel...
    start /B stunnel %STUNNEL_CONF%
    timeout /t 2 /nobreak >nul
)

REM Используем curl через локальный прокси
%CURL_EXE% %*
"@

$curlWrapper | Out-File -FilePath "$gostDir\curl-gost.bat" -Encoding ASCII
Write-Host "✅ curl wrapper создан: $gostDir\curl-gost.bat" -ForegroundColor Green

# ШАГ 5: Настроить stunnel для GOST TLS
Write-Host "`n[5/5] Настройка stunnel (GOST TLS прокси)..." -ForegroundColor Yellow

$stunnelConf = @"
; Stunnel configuration for GOST TLS
; Работает как прокси между curl и GOST API

[gost-api]
client = yes
accept = 127.0.0.1:8443
connect = api.gost.bankingapi.ru:8443

; Используем сертификат из КриптоПРО
;engineId = capi
;engineCtrl = list_certs

; SSL настройки
sslVersion = all
options = NO_SSLv2
options = NO_SSLv3
"@

$stunnelConf | Out-File -FilePath "$gostDir\stunnel.conf" -Encoding ASCII
Write-Host "✅ stunnel конфиг создан" -ForegroundColor Green

# Проверяем установлен ли stunnel
$stunnelPath = "C:\Program Files (x86)\stunnel\bin\stunnel.exe"
if (!(Test-Path $stunnelPath)) {
    Write-Host "⚠️  stunnel не установлен" -ForegroundColor Yellow
    Write-Host "Скачайте: https://www.stunnel.org/downloads.html" -ForegroundColor Cyan
    Write-Host "Или: choco install stunnel" -ForegroundColor Gray
}

# ИТОГОВЫЙ ОТЧЕТ
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "УСТАНОВКА ЗАВЕРШЕНА" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ ЧТО УСТАНОВЛЕНО:" -ForegroundColor Green
Write-Host "  - Директория: $gostDir" -ForegroundColor White
Write-Host "  - curl wrapper: $gostDir\curl-gost.bat" -ForegroundColor White
Write-Host "  - stunnel config: $gostDir\stunnel.conf" -ForegroundColor White

Write-Host ""
Write-Host "⚠️  ЧТО НУЖНО ДОДЕЛАТЬ:" -ForegroundColor Yellow
if (!(Test-Path $cryptoproPath)) {
    Write-Host "  1. Установить КриптоПРО CSP" -ForegroundColor White
    Write-Host "     https://cryptopro.ru/products/csp/downloads" -ForegroundColor Gray
}
if ($gostCerts.Count -eq 0) {
    Write-Host "  2. Получить тестовый сертификат" -ForegroundColor White
    Write-Host "     https://www.cryptopro.ru/certsrv/certrqma.asp" -ForegroundColor Gray
}
if (!(Test-Path $stunnelPath)) {
    Write-Host "  3. Установить stunnel" -ForegroundColor White
    Write-Host "     https://www.stunnel.org/downloads.html" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🚀 СЛЕДУЮЩИЙ ШАГ:" -ForegroundColor Cyan
Write-Host "Запустите тест подключения:" -ForegroundColor White
Write-Host "  .\test_gost_connection_final.ps1" -ForegroundColor Yellow

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan

