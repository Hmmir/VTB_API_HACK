# Запуск всех сервисов FinanceHub на Windows Server

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "🚀 Starting FinanceHub" -ForegroundColor Green
Write-Host "   Windows Server 2025" -ForegroundColor Cyan
Write-Host "   Domain: vtb.gistrec.cloud" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Green

# 1. PostgreSQL
Write-Host "📦 [1/4] Starting PostgreSQL..." -ForegroundColor Cyan
try {
    Restart-Service postgresql-x64-15 -ErrorAction Stop
    Write-Host "   ✅ PostgreSQL started" -ForegroundColor Green
    Start-Sleep -Seconds 3
} catch {
    Write-Host "   ⚠️ PostgreSQL service not found or already running" -ForegroundColor Yellow
}

# 2. Backend (через PM2)
Write-Host "`n🐍 [2/4] Starting Backend..." -ForegroundColor Cyan
cd $PSScriptRoot
try {
    pm2 restart financehub-backend 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   Starting Backend for the first time..." -ForegroundColor Yellow
        pm2 start ecosystem.config.js
    }
    Write-Host "   ✅ Backend started on port 8000" -ForegroundColor Green
    Start-Sleep -Seconds 5
} catch {
    Write-Host "   ❌ Failed to start Backend" -ForegroundColor Red
}

# 3. GOST Service (если настроен)
Write-Host "`n🔐 [3/4] Starting GOST Service (optional)..." -ForegroundColor Cyan
if (Test-Path ".\gost_windows_service.py") {
    try {
        pm2 restart financehub-gost 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   ⏭️ GOST Service not configured, skipping..." -ForegroundColor Yellow
        } else {
            Write-Host "   ✅ GOST Service started on port 5555" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ⏭️ GOST Service skipped" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⏭️ GOST Service not found, skipping..." -ForegroundColor Yellow
}
Start-Sleep -Seconds 2

# 4. Nginx
Write-Host "`n🌐 [4/4] Starting Nginx..." -ForegroundColor Cyan
$nginxPath = "C:\tools\nginx-1.24.0"
if (Test-Path $nginxPath) {
    try {
        cd $nginxPath
        # Проверяем, не запущен ли уже Nginx
        $nginxProcess = Get-Process nginx -ErrorAction SilentlyContinue
        if ($nginxProcess) {
            Write-Host "   🔄 Nginx already running, reloading..." -ForegroundColor Yellow
            .\nginx.exe -s reload
        } else {
            Start-Process nginx.exe -WindowStyle Hidden
            Write-Host "   ✅ Nginx started on port 80" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ⚠️ Failed to start Nginx: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    cd $PSScriptRoot
} else {
    Write-Host "   ⚠️ Nginx not found at $nginxPath" -ForegroundColor Yellow
}
Start-Sleep -Seconds 2

# 5. Проверка статуса
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ Services started!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "📊 PM2 Status:" -ForegroundColor Yellow
pm2 status

Write-Host "`n🌍 Access URLs:" -ForegroundColor Yellow
Write-Host "   Frontend:  http://vtb.gistrec.cloud" -ForegroundColor White
Write-Host "   Backend:   http://vtb.gistrec.cloud/api/v1" -ForegroundColor White
Write-Host "   API Docs:  http://vtb.gistrec.cloud/docs" -ForegroundColor White
Write-Host "   Swagger:   http://vtb.gistrec.cloud/openapi.json" -ForegroundColor White

Write-Host "`n🔑 Test Credentials:" -ForegroundColor Yellow
Write-Host "   Email:     team075-6@test.com" -ForegroundColor White
Write-Host "   Password:  password123" -ForegroundColor White

Write-Host "`n📝 Useful Commands:" -ForegroundColor Yellow
Write-Host "   View logs:      pm2 logs financehub-backend" -ForegroundColor White
Write-Host "   Restart:        pm2 restart financehub-backend" -ForegroundColor White
Write-Host "   Stop all:       .\stop-all.ps1" -ForegroundColor White
Write-Host "   Update app:     .\update.ps1" -ForegroundColor White

Write-Host "`n✨ Done! Application is ready." -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

