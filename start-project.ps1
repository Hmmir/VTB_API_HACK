#!/usr/bin/env pwsh
# FinanceHub - Quick Start Script

Write-Host "🚀 FinanceHub - Запуск проекта" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "📋 Проверка Docker..." -ForegroundColor Yellow
$dockerRunning = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        docker ps > $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerRunning = $true
            break
        }
    } catch {}
    
    if ($i -eq 1) {
        Write-Host "⏳ Ожидание запуска Docker Desktop..." -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 2
    Write-Host "." -NoNewline
}

Write-Host ""

if (-not $dockerRunning) {
    Write-Host "❌ Docker не запущен. Запустите Docker Desktop и повторите попытку." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker запущен!" -ForegroundColor Green
Write-Host ""

# Создание .env файлов если их нет
if (-not (Test-Path "backend\.env")) {
    Write-Host "📝 Создание backend/.env..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env" -ErrorAction SilentlyContinue
    
    # Генерация ключей
    $secretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
    $encryptionKey = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    
    # Обновление .env с ключами
    $envContent = Get-Content "backend\.env" -Raw
    $envContent = $envContent -replace "SECRET_KEY=.*", "SECRET_KEY=$secretKey"
    $envContent = $envContent -replace "ENCRYPTION_KEY=.*", "ENCRYPTION_KEY=$encryptionKey"
    $envContent = $envContent -replace "VTB_TEAM_ID=.*", "VTB_TEAM_ID=team010-1"
    $envContent | Set-Content "backend\.env" -NoNewline
}

if (-not (Test-Path "frontend\.env")) {
    Write-Host "📝 Создание frontend/.env..." -ForegroundColor Yellow
    Copy-Item "frontend\.env.example" "frontend\.env" -ErrorAction SilentlyContinue
}

Write-Host "✅ Конфигурация готова!" -ForegroundColor Green
Write-Host ""

# Остановка старых контейнеров
Write-Host "🛑 Остановка старых контейнеров (если есть)..." -ForegroundColor Yellow
docker-compose down -v 2>$null
Write-Host ""

# Запуск контейнеров
Write-Host "🐳 Запуск Docker контейнеров..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка запуска контейнеров" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Контейнеры запущены!" -ForegroundColor Green
Write-Host ""

# Ожидание готовности PostgreSQL
Write-Host "⏳ Ожидание готовности PostgreSQL..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

for ($i = 1; $i -le 30; $i++) {
    $pgReady = docker-compose exec -T postgres pg_isready -U financehub 2>$null
    if ($LASTEXITCODE -eq 0) {
        break
    }
    Start-Sleep -Seconds 2
    Write-Host "." -NoNewline
}

Write-Host ""
Write-Host "✅ PostgreSQL готов!" -ForegroundColor Green
Write-Host ""

# Применение миграций
Write-Host "🔧 Применение миграций базы данных..." -ForegroundColor Yellow
docker-compose exec -T backend alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Миграции не применены (возможно БД уже настроена)" -ForegroundColor Yellow
} else {
    Write-Host "✅ Миграции применены!" -ForegroundColor Green
}
Write-Host ""

# Заполнение демо-данных
Write-Host "🌱 Заполнение демо-данных..." -ForegroundColor Yellow
docker-compose exec -T backend python scripts/seed_demo_data.py 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Демо-данные не загружены (возможно уже есть)" -ForegroundColor Yellow
} else {
    Write-Host "✅ Демо-данные загружены!" -ForegroundColor Green
}
Write-Host ""

# Финальная информация
Write-Host "=" -ForegroundColor Green -NoNewline
Write-Host "=" * 50 -ForegroundColor Green
Write-Host "🎉 Проект успешно запущен!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Green -NoNewline
Write-Host "=" * 50 -ForegroundColor Green
Write-Host ""
Write-Host "📱 Frontend:       " -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔧 Backend API:    " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs:       " -NoNewline
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "📖 ReDoc:          " -NoNewline
Write-Host "http://localhost:8000/redoc" -ForegroundColor Cyan
Write-Host ""
Write-Host "🏦 Доступные банки для подключения:" -ForegroundColor Yellow
Write-Host "   • VBank (Virtual Bank) - vbank" -ForegroundColor White
Write-Host "   • ABank (Awesome Bank) - abank" -ForegroundColor White
Write-Host "   • SBank (Smart Bank) - sbank" -ForegroundColor White
Write-Host ""
Write-Host "📋 Полезные команды:" -ForegroundColor Yellow
Write-Host "   • docker-compose logs -f          - Просмотр логов" -ForegroundColor White
Write-Host "   • docker-compose restart          - Перезапуск" -ForegroundColor White
Write-Host "   • docker-compose down             - Остановка" -ForegroundColor White
Write-Host "   • docker-compose exec backend ... - Команды в backend" -ForegroundColor White
Write-Host ""
Write-Host "✨ Готово к тестированию! Откройте браузер на http://localhost:3000" -ForegroundColor Green
Write-Host ""

