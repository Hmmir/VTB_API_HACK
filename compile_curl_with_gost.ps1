# Компиляция curl с OpenSSL GOST

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "КОМПИЛЯЦИЯ CURL С OPENSSL GOST" -ForegroundColor Yellow
Write-Host "============================================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

# Пути
$curlSource = "C:\curl-src"
$opensslDir = "C:\OpenSSL-GOST-Shared"
$curlInstallDir = "C:\curl-gost"

# Шаг 1: Клонировать curl
Write-Host "[1/5] Клонирование curl..." -ForegroundColor Cyan
if (!(Test-Path $curlSource)) {
    git clone https://github.com/curl/curl.git $curlSource
    Write-Host "✅ curl клонирован" -ForegroundColor Green
} else {
    Write-Host "✅ curl уже клонирован" -ForegroundColor Green
}

# Шаг 2: Перейти в папку curl
Set-Location $curlSource
Write-Host "✅ Перешли в: $curlSource" -ForegroundColor Green

# Шаг 3: Запустить Developer Command Prompt
Write-Host "`n[2/5] Настройка Visual Studio окружения..." -ForegroundColor Cyan
$vsPath = "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if (Test-Path $vsPath) {
    Write-Host "✅ Visual Studio найден" -ForegroundColor Green
} else {
    Write-Host "❌ Visual Studio не найден" -ForegroundColor Red
    Write-Host "Установите Visual Studio 2022 Community" -ForegroundColor Yellow
    exit 1
}

# Шаг 4: Создать build директорию
Write-Host "`n[3/5] Подготовка сборки..." -ForegroundColor Cyan
if (!(Test-Path "$curlSource\build")) {
    New-Item -ItemType Directory -Path "$curlSource\build" | Out-Null
}
Set-Location "$curlSource\build"
Write-Host "✅ Build директория создана" -ForegroundColor Green

# Шаг 5: CMake конфигурация
Write-Host "`n[4/5] Конфигурация CMake..." -ForegroundColor Cyan
Write-Host "OpenSSL: $opensslDir" -ForegroundColor Gray
Write-Host "Install: $curlInstallDir" -ForegroundColor Gray

cmake .. `
    -G "Visual Studio 17 2022" `
    -A x64 `
    -DCMAKE_INSTALL_PREFIX="$curlInstallDir" `
    -DCURL_USE_OPENSSL=ON `
    -DOPENSSL_ROOT_DIR="$opensslDir" `
    -DOPENSSL_INCLUDE_DIR="$opensslDir\include" `
    -DOPENSSL_CRYPTO_LIBRARY="$opensslDir\lib\libcrypto.lib" `
    -DOPENSSL_SSL_LIBRARY="$opensslDir\lib\libssl.lib" `
    -DBUILD_CURL_EXE=ON `
    -DBUILD_SHARED_LIBS=OFF

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ CMake конфигурация не удалась" -ForegroundColor Red
    exit 1
}
Write-Host "✅ CMake конфигурация завершена" -ForegroundColor Green

# Шаг 6: Сборка
Write-Host "`n[5/5] Сборка curl..." -ForegroundColor Cyan
Write-Host "Это может занять 5-10 минут..." -ForegroundColor Yellow

cmake --build . --config Release --target curl

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Сборка не удалась" -ForegroundColor Red
    exit 1
}
Write-Host "✅ curl собран" -ForegroundColor Green

# Шаг 7: Установка
Write-Host "`nУстановка curl..." -ForegroundColor Cyan
cmake --install . --config Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Установка не удалась" -ForegroundColor Red
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "✅ УСПЕШНО!" -ForegroundColor Green -BackgroundColor DarkGreen
Write-Host "============================================================" -ForegroundColor Green
Write-Host "`ncurl установлен в: $curlInstallDir\bin\curl.exe" -ForegroundColor White
Write-Host "`nПроверка версии:" -ForegroundColor Cyan
& "$curlInstallDir\bin\curl.exe" --version

Write-Host "`n📋 СЛЕДУЮЩИЙ ШАГ:" -ForegroundColor Yellow
Write-Host "Запустить: test_gost_with_our_curl.bat" -ForegroundColor White

