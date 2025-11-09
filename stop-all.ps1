# Остановка всех сервисов FinanceHub

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Red
Write-Host "⏸️ Stopping FinanceHub" -ForegroundColor Red
Write-Host "========================================`n" -ForegroundColor Red

# 1. Nginx
Write-Host "🌐 [1/3] Stopping Nginx..." -ForegroundColor Cyan
$nginxPath = "C:\tools\nginx-1.24.0"
if (Test-Path $nginxPath) {
    try {
        cd $nginxPath
        .\nginx.exe -s stop
        Write-Host "   ✅ Nginx stopped" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️ Nginx was not running" -ForegroundColor Yellow
    }
    cd $PSScriptRoot
}

# 2. Backend & GOST (PM2)
Write-Host "`n🐍 [2/3] Stopping Backend & GOST..." -ForegroundColor Cyan
try {
    pm2 stop all
    Write-Host "   ✅ All PM2 processes stopped" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ No PM2 processes running" -ForegroundColor Yellow
}

# 3. PostgreSQL (опционально - можно не останавливать)
Write-Host "`n📦 [3/3] PostgreSQL..." -ForegroundColor Cyan
Write-Host "   ℹ️ PostgreSQL left running (optional to stop)" -ForegroundColor Yellow
# Uncomment to stop PostgreSQL:
# Stop-Service postgresql-x64-15

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ All services stopped!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "📝 To restart: .\start-all.ps1`n" -ForegroundColor Cyan

