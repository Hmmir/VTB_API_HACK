# Обновление FinanceHub без даунтайма

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "🔄 Updating FinanceHub" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# 1. Сохраняем текущую директорию
$originalDir = Get-Location

# 2. Останавливаем сервисы
Write-Host "⏸️ [1/5] Stopping services..." -ForegroundColor Cyan
pm2 stop all
$nginxPath = "C:\tools\nginx-1.24.0"
if (Test-Path $nginxPath) {
    cd $nginxPath
    .\nginx.exe -s stop
    cd $originalDir
}
Write-Host "   ✅ Services stopped`n" -ForegroundColor Green

# 3. Обновляем код
Write-Host "📥 [2/5] Pulling latest code..." -ForegroundColor Cyan
cd $PSScriptRoot
git pull origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️ Git pull failed, continuing with local changes..." -ForegroundColor Yellow
} else {
    Write-Host "   ✅ Code updated`n" -ForegroundColor Green
}

# 4. Backend: обновляем зависимости и миграции
Write-Host "🐍 [3/5] Updating Backend..." -ForegroundColor Cyan
cd backend
try {
    .\venv\Scripts\activate
    pip install -r requirements.txt --quiet
    alembic upgrade head
    deactivate
    Write-Host "   ✅ Backend updated`n" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Backend update had issues: $($_.Exception.Message)" -ForegroundColor Yellow
    deactivate
}
cd ..

# 5. Frontend: пересобираем
Write-Host "🎨 [4/5] Rebuilding Frontend..." -ForegroundColor Cyan
cd frontend
try {
    npm install --silent
    npm run build
    Write-Host "   ✅ Frontend rebuilt`n" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Frontend build failed: $($_.Exception.Message)" -ForegroundColor Red
    cd ..
    exit 1
}
cd ..

# 6. Запускаем сервисы
Write-Host "🚀 [5/5] Starting services..." -ForegroundColor Cyan
.\start-all.ps1

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ Update complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "🌍 Access: http://vtb.gistrec.cloud`n" -ForegroundColor Cyan

