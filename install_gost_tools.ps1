# Скрипт установки GOST инструментов для VTB API Hackathon

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Установка GOST инструментов" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Шаг 1: Получение тестового сертификата
Write-Host "`n[1/3] Получение тестового сертификата КриптоПРО..." -ForegroundColor Yellow
Write-Host "Откройте в браузере: https://www.cryptopro.ru/certsrv/certrqxt.asp" -ForegroundColor Green
Write-Host "Используйте контейнер: VTB_Test_Container" -ForegroundColor Green

# Шаг 2: Скачивание OpenSSL GOST
Write-Host "`n[2/3] Скачивание OpenSSL с GOST..." -ForegroundColor Yellow
$opensslUrl = "https://github.com/gost-engine/engine/releases/download/v3.0.3/gost-engine-3.0.3-windows-x64.zip"
$opensslPath = "$env:TEMP\gost-openssl.zip"

try {
    Write-Host "Скачиваю OpenSSL GOST..." -ForegroundColor Green
    Invoke-WebRequest -Uri $opensslUrl -OutFile $opensslPath -UseBasicParsing
    Write-Host "✅ Скачано: $opensslPath" -ForegroundColor Green
} catch {
    Write-Host "❌ Ошибка скачивания. Попробуйте вручную:" -ForegroundColor Red
    Write-Host "   $opensslUrl" -ForegroundColor Yellow
}

# Шаг 3: Скачивание curl с GOST
Write-Host "`n[3/3] Скачивание curl с GOST..." -ForegroundColor Yellow
Write-Host "curl нужно скомпилировать с OpenSSL GOST" -ForegroundColor Yellow

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Следующие шаги:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "1. Получите сертификат через браузер" -ForegroundColor White
Write-Host "2. Распакуйте OpenSSL GOST" -ForegroundColor White
Write-Host "3. Скомпилируйте curl с OpenSSL GOST" -ForegroundColor White
Write-Host "4. Протестируйте подключение" -ForegroundColor White

