# 🚀 Быстрый деплой для Windows Server 2025
# Для использования на сервере 178.20.42.63

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 FinanceHub - Quick Deploy" -ForegroundColor Cyan
Write-Host "   vtb.gistrec.cloud" -ForegroundColor White
Write-Host "========================================`n" -ForegroundColor Cyan

# Вариант 1: Полная автоматическая установка
Write-Host "📦 Option 1: Full Automatic Install" -ForegroundColor Green
Write-Host "   Run: .\install.ps1`n" -ForegroundColor White

# Вариант 2: Ручная установка
Write-Host "🔧 Option 2: Manual Install (5 minutes)" -ForegroundColor Yellow
Write-Host @"
   
   Step 1: Install Chocolatey
   ---------------------------
   Set-ExecutionPolicy Bypass -Scope Process -Force
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   
   Step 2: Install Software
   -------------------------
   choco install git python311 nodejs-lts postgresql15 nginx -y
   npm install -g pm2
   
   Step 3: Clone & Setup
   ---------------------
   cd C:\Projects
   git clone https://github.com/Hmmir/VTB_API_HACK.git
   cd VTB_API_HACK
   
   Step 4: Setup Backend
   ---------------------
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   
   Step 5: Setup Frontend
   ----------------------
   cd ..\frontend
   npm install
   npm run build
   
   Step 6: Start Services
   ----------------------
   cd ..
   .\start-all.ps1

"@ -ForegroundColor White

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Choose your option and proceed!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Спрашиваем пользователя
$choice = Read-Host "Choose option (1 for auto, 2 for manual, or Q to quit)"

switch ($choice) {
    "1" {
        Write-Host "`n🚀 Starting automatic installation...`n" -ForegroundColor Green
        .\install.ps1
    }
    "2" {
        Write-Host "`n📝 Follow the manual steps above.`n" -ForegroundColor Yellow
    }
    default {
        Write-Host "`n👋 Goodbye!`n" -ForegroundColor White
    }
}

