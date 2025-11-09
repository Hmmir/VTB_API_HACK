# ========================================
# АВТОМАТИЧЕСКИЙ ДЕПЛОЙ НА WINDOWS SERVER
# vtb.gistrec.cloud (178.20.42.63)
# ========================================

param(
    [switch]$SkipSoftware = $false
)

$ErrorActionPreference = "Continue"

Write-Host @"

========================================
🚀 FinanceHub Auto Deploy
   vtb.gistrec.cloud
========================================

"@ -ForegroundColor Cyan

# Проверка прав администратора
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ Нужны права администратора!" -ForegroundColor Red
    Write-Host "   Запустите PowerShell от имени Администратора`n" -ForegroundColor Yellow
    exit 1
}

# ============================================
# ШАГ 1: УСТАНОВКА CHOCOLATEY
# ============================================
Write-Host "`n[1/8] Установка Chocolatey..." -ForegroundColor Cyan
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "   Устанавливаю Chocolatey..." -ForegroundColor Gray
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    try {
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Write-Host "   ✅ Chocolatey установлен" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Ошибка установки Chocolatey: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ Chocolatey уже установлен" -ForegroundColor Green
}

# ============================================
# ШАГ 2: УСТАНОВКА НЕОБХОДИМОГО ПО
# ============================================
if (-not $SkipSoftware) {
    Write-Host "`n[2/8] Установка необходимого ПО..." -ForegroundColor Cyan
    Write-Host "   Это займет 5-10 минут. Подождите...`n" -ForegroundColor Yellow
    
    $packages = @{
        "git" = "Система контроля версий"
        "python311" = "Python 3.11"
        "nodejs-lts" = "Node.js 20 LTS"
        "postgresql15" = "PostgreSQL 15"
    }
    
    foreach ($pkg in $packages.GetEnumerator()) {
        Write-Host "   📦 Устанавливаю $($pkg.Value)..." -ForegroundColor Gray
        if ($pkg.Key -eq "postgresql15") {
            choco install $pkg.Key -y --params "/Password:financehub_password" --force --no-progress 2>$null | Out-Null
        } else {
            choco install $pkg.Key -y --force --no-progress 2>$null | Out-Null
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "      ✅ $($pkg.Value)" -ForegroundColor Green
        }
    }
    
    # Обновляем PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # PM2 для управления процессами
    Write-Host "   📦 Устанавливаю PM2..." -ForegroundColor Gray
    npm install -g pm2 --silent 2>$null
    Write-Host "      ✅ PM2 установлен" -ForegroundColor Green
    
    Write-Host "`n   ✅ Все ПО установлено" -ForegroundColor Green
} else {
    Write-Host "`n[2/8] Пропускаю установку ПО (используется --SkipSoftware)" -ForegroundColor Yellow
}

# ============================================
# ШАГ 3: КЛОНИРОВАНИЕ РЕПОЗИТОРИЯ
# ============================================
Write-Host "`n[3/8] Клонирование репозитория..." -ForegroundColor Cyan
$projectDir = "C:\Projects\VTB_API_HACK"

if (Test-Path $projectDir) {
    Write-Host "   Проект уже существует, обновляю..." -ForegroundColor Yellow
    cd $projectDir
    git pull origin main 2>$null
} else {
    Write-Host "   Клонирую из GitHub..." -ForegroundColor Gray
    New-Item -ItemType Directory -Path "C:\Projects" -Force | Out-Null
    cd C:\Projects
    git clone https://github.com/Hmmir/VTB_API_HACK.git 2>$null
    cd VTB_API_HACK
}
Write-Host "   ✅ Репозиторий готов" -ForegroundColor Green

# ============================================
# ШАГ 4: НАСТРОЙКА POSTGRESQL
# ============================================
Write-Host "`n[4/8] Настройка PostgreSQL..." -ForegroundColor Cyan

# Ждем запуска PostgreSQL
Write-Host "   Ожидаю запуска PostgreSQL..." -ForegroundColor Gray
Start-Sleep -Seconds 5

$psqlPath = "C:\Program Files\PostgreSQL\15\bin\psql.exe"
if (Test-Path $psqlPath) {
    # Создаем SQL для инициализации
    $sqlCommands = @"
CREATE DATABASE financehub;
CREATE USER financehub_user WITH PASSWORD 'financehub_password';
GRANT ALL PRIVILEGES ON DATABASE financehub TO financehub_user;
ALTER DATABASE financehub OWNER TO financehub_user;

CREATE DATABASE mybank;
CREATE USER mybank_user WITH PASSWORD 'mybank_password';
GRANT ALL PRIVILEGES ON DATABASE mybank TO mybank_user;
ALTER DATABASE mybank OWNER TO mybank_user;
"@
    
    $sqlCommands | Out-File -FilePath "$env:TEMP\init_db.sql" -Encoding UTF8
    
    $env:PGPASSWORD = "financehub_password"
    & $psqlPath -U postgres -f "$env:TEMP\init_db.sql" 2>$null
    
    Remove-Item "$env:TEMP\init_db.sql" -Force -ErrorAction SilentlyContinue
    
    Write-Host "   ✅ PostgreSQL настроен" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ PostgreSQL не найден, пропускаю" -ForegroundColor Yellow
}

# ============================================
# ШАГ 5: НАСТРОЙКА BACKEND
# ============================================
Write-Host "`n[5/8] Настройка Backend..." -ForegroundColor Cyan
cd $projectDir\backend

# Создаем .env
$envContent = @"
DATABASE_URL=postgresql://financehub_user:financehub_password@localhost:5432/financehub
SECRET_KEY=production-secret-key-$(Get-Random)-$(Get-Random)
ENCRYPTION_KEY=32chars-encryption-key-prod-$(Get-Random)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

VTB_API_BASE_URL=https://ift.rtuitlab.dev
VTB_TEAM_ID=team075
VTB_TEAM_SECRET=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di

USE_GOST=false
GOST_API_URL=https://api.gost.bankingapi.ru:8443

MYBANK_API_URL=http://localhost:8001

APP_NAME=FinanceHub
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=http://vtb.gistrec.cloud,https://vtb.gistrec.cloud,http://localhost:3000
"@

$envContent | Out-File -FilePath ".\.env" -Encoding UTF8 -NoNewline

Write-Host "   Создаю виртуальное окружение..." -ForegroundColor Gray
python -m venv venv 2>$null

Write-Host "   Устанавливаю зависимости..." -ForegroundColor Gray
.\venv\Scripts\activate
python -m pip install --upgrade pip --quiet 2>$null
pip install -r requirements.txt --quiet 2>$null

Write-Host "   Применяю миграции..." -ForegroundColor Gray
alembic upgrade head 2>$null

# Заполняем тестовыми данными
if (Test-Path ".\scripts\seed_demo_data.py") {
    Write-Host "   Загружаю тестовые данные..." -ForegroundColor Gray
    python scripts\seed_demo_data.py 2>$null
}

deactivate
Write-Host "   ✅ Backend настроен" -ForegroundColor Green

# ============================================
# ШАГ 6: НАСТРОЙКА FRONTEND
# ============================================
Write-Host "`n[6/8] Настройка Frontend..." -ForegroundColor Cyan
cd $projectDir\frontend

# Создаем .env.production
"VITE_API_URL=http://vtb.gistrec.cloud/api/v1" | Out-File -FilePath ".\.env.production" -Encoding UTF8 -NoNewline

Write-Host "   Устанавливаю зависимости..." -ForegroundColor Gray
npm install --silent 2>$null

Write-Host "   Собираю production билд..." -ForegroundColor Gray
npm run build 2>$null

Write-Host "   ✅ Frontend собран" -ForegroundColor Green

# ============================================
# ШАГ 7: НАСТРОЙКА PM2 И ЗАПУСК
# ============================================
Write-Host "`n[7/8] Настройка PM2 и запуск сервисов..." -ForegroundColor Cyan
cd $projectDir

# Создаем ecosystem.config.js
$pm2Config = @"
module.exports = {
  apps: [
    {
      name: 'financehub-backend',
      script: '$projectDir\\backend\\venv\\Scripts\\python.exe',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      cwd: '$projectDir\\backend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
      },
    },
    {
      name: 'financehub-frontend',
      script: 'C:\\Program Files\\nodejs\\npx.cmd',
      args: 'serve -s dist -l 3000',
      cwd: '$projectDir\\frontend',
      instances: 1,
      autorestart: true,
      watch: false,
    },
  ],
};
"@

$pm2Config | Out-File -FilePath ".\ecosystem.config.js" -Encoding UTF8

# Устанавливаем serve для фронтенда
npm install -g serve --silent 2>$null

# Останавливаем старые процессы
pm2 delete all 2>$null

# Запускаем новые
Write-Host "   Запускаю Backend..." -ForegroundColor Gray
pm2 start ecosystem.config.js 2>$null
Start-Sleep -Seconds 5

Write-Host "   ✅ Сервисы запущены" -ForegroundColor Green

# Сохраняем конфигурацию PM2
pm2 save 2>$null

# ============================================
# ШАГ 8: НАСТРОЙКА FIREWALL
# ============================================
Write-Host "`n[8/8] Настройка Windows Firewall..." -ForegroundColor Cyan

$ports = @(
    @{Port=80; Name="HTTP"},
    @{Port=443; Name="HTTPS"},
    @{Port=3000; Name="Frontend"},
    @{Port=8000; Name="Backend API"}
)

foreach ($p in $ports) {
    $ruleName = "FinanceHub - Allow $($p.Name)"
    
    # Удаляем старое правило если есть
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue 2>$null
    
    # Создаем новое
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $p.Port -Action Allow -ErrorAction SilentlyContinue 2>$null
}

Write-Host "   ✅ Firewall настроен" -ForegroundColor Green

# ============================================
# ФИНАЛ: ПРОВЕРКА И СТАТУС
# ============================================
Write-Host @"

========================================
✅ ДЕПЛОЙ ЗАВЕРШЕН!
========================================

"@ -ForegroundColor Green

# Статус сервисов
Write-Host "📊 Статус сервисов:" -ForegroundColor Yellow
pm2 status

Write-Host "`n🌍 Доступ к приложению:" -ForegroundColor Yellow
Write-Host "   Frontend:   http://vtb.gistrec.cloud:3000" -ForegroundColor White
Write-Host "   Backend:    http://vtb.gistrec.cloud:8000" -ForegroundColor White
Write-Host "   API Docs:   http://vtb.gistrec.cloud:8000/docs" -ForegroundColor White

Write-Host "`n🔑 Тестовый доступ:" -ForegroundColor Yellow
Write-Host "   Email:      team075-6@test.com" -ForegroundColor White
Write-Host "   Password:   password123" -ForegroundColor White

Write-Host "`n📝 Полезные команды:" -ForegroundColor Yellow
Write-Host "   pm2 status                    - статус сервисов" -ForegroundColor White
Write-Host "   pm2 logs financehub-backend   - логи backend" -ForegroundColor White
Write-Host "   pm2 logs financehub-frontend  - логи frontend" -ForegroundColor White
Write-Host "   pm2 restart all               - перезапуск всех сервисов" -ForegroundColor White

Write-Host "`n🎯 Следующие шаги:" -ForegroundColor Yellow
Write-Host "   1. Откройте браузер: http://vtb.gistrec.cloud:3000" -ForegroundColor White
Write-Host "   2. Войдите с тестовым аккаунтом" -ForegroundColor White
Write-Host "   3. Запишите демо-видео!" -ForegroundColor White

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "🚀 Приложение готово к использованию!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# Открываем браузер
Write-Host "Открываю браузер через 3 секунды..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
Start-Process "http://vtb.gistrec.cloud:3000"

