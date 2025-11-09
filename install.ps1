# Автоматическая установка FinanceHub на Windows Server 2025

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "🚀 FinanceHub - Quick Install" -ForegroundColor Green
Write-Host "   Windows Server 2025 Edition" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Green

# Проверка прав администратора
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "   Please run PowerShell as Administrator and try again.`n" -ForegroundColor Yellow
    exit 1
}

# 1. Установка Chocolatey
Write-Host "📦 [1/7] Installing Chocolatey..." -ForegroundColor Cyan
try {
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        Write-Host "   ✅ Chocolatey installed`n" -ForegroundColor Green
    } else {
        Write-Host "   ✅ Chocolatey already installed`n" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Failed to install Chocolatey: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Обновляем PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 2. Установка необходимого ПО
Write-Host "📦 [2/7] Installing required software..." -ForegroundColor Cyan
Write-Host "   This may take 10-15 minutes...`n" -ForegroundColor Yellow

$packages = @(
    @{Name="git"; Params=""},
    @{Name="python311"; Params=""},
    @{Name="nodejs-lts"; Params=""},
    @{Name="postgresql15"; Params="/Password:financehub_password"},
    @{Name="nginx"; Params=""}
)

foreach ($package in $packages) {
    Write-Host "   Installing $($package.Name)..." -ForegroundColor Gray
    if ($package.Params) {
        choco install $package.Name -y --params $package.Params --force
    } else {
        choco install $package.Name -y --force
    }
}

Write-Host "   ✅ All packages installed`n" -ForegroundColor Green

# Обновляем PATH снова после установки
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Установка PM2 глобально
Write-Host "   Installing PM2..." -ForegroundColor Gray
npm install -g pm2 --silent
Write-Host "   ✅ PM2 installed`n" -ForegroundColor Green

# 3. Клонирование репозитория
Write-Host "📥 [3/7] Cloning repository..." -ForegroundColor Cyan
$projectsDir = "C:\Projects"
if (-not (Test-Path $projectsDir)) {
    New-Item -ItemType Directory -Path $projectsDir -Force | Out-Null
}

cd $projectsDir
if (Test-Path "VTB_API_HACK") {
    Write-Host "   Repository already exists, updating..." -ForegroundColor Yellow
    cd VTB_API_HACK
    git pull origin main
} else {
    git clone https://github.com/Hmmir/VTB_API_HACK.git
    cd VTB_API_HACK
}
Write-Host "   ✅ Repository ready`n" -ForegroundColor Green

# 4. Настройка PostgreSQL
Write-Host "🗄️ [4/7] Setting up PostgreSQL..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Создаем SQL файл для инициализации
$sqlInit = @"
CREATE DATABASE financehub;
CREATE USER financehub_user WITH PASSWORD 'financehub_password';
GRANT ALL PRIVILEGES ON DATABASE financehub TO financehub_user;

CREATE DATABASE mybank;
CREATE USER mybank_user WITH PASSWORD 'mybank_password';
GRANT ALL PRIVILEGES ON DATABASE mybank TO mybank_user;
"@

$sqlInit | Out-File -FilePath ".\init.sql" -Encoding utf8

try {
    & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -f ".\init.sql" -q 2>$null
    Write-Host "   ✅ PostgreSQL configured`n" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ PostgreSQL setup had issues (may already be configured)`n" -ForegroundColor Yellow
}

Remove-Item ".\init.sql" -Force -ErrorAction SilentlyContinue

# 5. Настройка Backend
Write-Host "🐍 [5/7] Setting up Backend..." -ForegroundColor Cyan
cd backend

# Создаем .env файл
$envContent = @"
DATABASE_URL=postgresql://financehub_user:financehub_password@localhost:5432/financehub
SECRET_KEY=super-secret-key-for-production-$(Get-Random)
ENCRYPTION_KEY=32-char-encryption-key-prod-$(Get-Random)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

VTB_API_BASE_URL=https://ift.rtuitlab.dev
VTB_TEAM_ID=team075
VTB_TEAM_SECRET=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di

USE_GOST=false
GOST_API_URL=https://api.gost.bankingapi.ru:8443
BANKING_API_URL=https://api.bankingapi.ru
AUTH_API_URL=https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token

MYBANK_API_URL=http://localhost:8001

APP_NAME=FinanceHub
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
"@

$envContent | Out-File -FilePath ".\.env" -Encoding utf8

# Создаем виртуальное окружение
python -m venv venv
.\venv\Scripts\activate

# Устанавливаем зависимости
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Применяем миграции
alembic upgrade head

# Заполняем тестовыми данными (если скрипт существует)
if (Test-Path ".\scripts\seed_demo_data.py") {
    python scripts\seed_demo_data.py
}

deactivate
Write-Host "   ✅ Backend configured`n" -ForegroundColor Green
cd ..

# 6. Настройка Frontend
Write-Host "🎨 [6/7] Setting up Frontend..." -ForegroundColor Cyan
cd frontend

# Создаем .env.production
$frontendEnv = "VITE_API_URL=http://vtb.gistrec.cloud/api/v1"
$frontendEnv | Out-File -FilePath ".\.env.production" -Encoding utf8

# Устанавливаем зависимости
npm install --silent

# Собираем production билд
npm run build

Write-Host "   ✅ Frontend built`n" -ForegroundColor Green
cd ..

# 7. Создаем ecosystem.config.js для PM2
Write-Host "⚙️ Creating PM2 configuration..." -ForegroundColor Cyan
$pm2Config = @"
module.exports = {
  apps: [
    {
      name: 'financehub-backend',
      script: 'C:\\Projects\\VTB_API_HACK\\backend\\venv\\Scripts\\python.exe',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      cwd: 'C:\\Projects\\VTB_API_HACK\\backend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
      },
    },
  ],
};
"@

$pm2Config | Out-File -FilePath ".\ecosystem.config.js" -Encoding utf8
Write-Host "   ✅ PM2 config created`n" -ForegroundColor Green

# 8. Настройка Nginx
Write-Host "🌐 [7/7] Configuring Nginx..." -ForegroundColor Cyan
$nginxConf = @"
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    access_log  logs/access.log;
    error_log   logs/error.log;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    upstream backend {
        server 127.0.0.1:8000;
    }

    server {
        listen       80;
        server_name  vtb.gistrec.cloud;

        client_max_body_size 10M;

        location / {
            root   C:/Projects/VTB_API_HACK/frontend/dist;
            index  index.html;
            try_files `$uri `$uri/ /index.html;
        }

        location /api {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade `$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto `$scheme;
            proxy_cache_bypass `$http_upgrade;
            proxy_read_timeout 300s;
            proxy_connect_timeout 300s;
        }

        location /docs {
            proxy_pass http://backend;
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
        }

        location /openapi.json {
            proxy_pass http://backend;
            proxy_set_header Host `$host;
        }
    }
}
"@

$nginxPath = "C:\tools\nginx-1.24.0"
if (Test-Path $nginxPath) {
    $nginxConf | Out-File -FilePath "$nginxPath\conf\nginx.conf" -Encoding utf8
    Write-Host "   ✅ Nginx configured`n" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ Nginx path not found, skipping config`n" -ForegroundColor Yellow
}

# 9. Настройка Firewall
Write-Host "🔥 Configuring Windows Firewall..." -ForegroundColor Cyan
try {
    New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "Allow HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow -ErrorAction SilentlyContinue
    Write-Host "   ✅ Firewall rules added`n" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Firewall rules may already exist`n" -ForegroundColor Yellow
}

# 10. Запуск сервисов
Write-Host "========================================" -ForegroundColor Green
Write-Host "🚀 Starting services..." -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

.\start-all.ps1

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ Installation Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Open browser: http://vtb.gistrec.cloud" -ForegroundColor White
Write-Host "   2. Login with: team075-6@test.com / password123" -ForegroundColor White
Write-Host "   3. Check API docs: http://vtb.gistrec.cloud/docs" -ForegroundColor White

Write-Host "`n🔧 Management commands:" -ForegroundColor Yellow
Write-Host "   Start:   .\start-all.ps1" -ForegroundColor White
Write-Host "   Stop:    .\stop-all.ps1" -ForegroundColor White
Write-Host "   Update:  .\update.ps1" -ForegroundColor White
Write-Host "   Logs:    pm2 logs financehub-backend" -ForegroundColor White

Write-Host "`n✨ Enjoy FinanceHub!`n" -ForegroundColor Green

