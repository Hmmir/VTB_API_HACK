# 🚀 Деплой на Windows Server 2025 (vtb.gistrec.cloud)

## 📋 Информация о сервере

```
IP: 178.20.42.63
Login: Administrator
Password: 2:5w35V-kJtYj+Bu45U9
Domain: vtb.gistrec.cloud
OS: Windows Server 2025
CPU: 2 cores
RAM: 4 GB
```

---

## 🎯 План деплоя

1. ✅ Установить необходимое ПО
2. ✅ Склонировать репозиторий
3. ✅ Настроить PostgreSQL
4. ✅ Настроить Backend (FastAPI)
5. ✅ Настроить Frontend (React)
6. ✅ Настроить GOST Service (опционально)
7. ✅ Настроить Nginx/IIS для reverse proxy
8. ✅ Настроить файрвол
9. ✅ Запустить все сервисы

---

## 📦 Шаг 1: Установка необходимого ПО

### 1.1 Установить Chocolatey (пакетный менеджер)

Откройте PowerShell от имени Администратора:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### 1.2 Установить все необходимые пакеты

```powershell
# Git
choco install git -y

# Python 3.11
choco install python311 -y

# Node.js 20 LTS
choco install nodejs-lts -y

# PostgreSQL 15
choco install postgresql15 -y --params '/Password:financehub_password'

# Nginx (для reverse proxy)
choco install nginx -y

# PM2 (для управления процессами)
npm install -g pm2
npm install -g pm2-windows-service

# Перезагружаем переменные окружения
refreshenv
```

### 1.3 Проверка установки

```powershell
git --version
python --version
node --version
npm --version
psql --version
nginx -v
pm2 --version
```

---

## 🔧 Шаг 2: Клонирование репозитория

```powershell
# Создаем директорию для проектов
New-Item -ItemType Directory -Path "C:\Projects" -Force
cd C:\Projects

# Клонируем репозиторий
git clone https://github.com/Hmmir/VTB_API_HACK.git
cd VTB_API_HACK
```

---

## 🗄️ Шаг 3: Настройка PostgreSQL

### 3.1 Создание баз данных

```powershell
# Подключаемся к PostgreSQL (пароль: financehub_password)
psql -U postgres

# В psql консоли:
CREATE DATABASE financehub;
CREATE USER financehub_user WITH PASSWORD 'financehub_password';
GRANT ALL PRIVILEGES ON DATABASE financehub TO financehub_user;

CREATE DATABASE mybank;
CREATE USER mybank_user WITH PASSWORD 'mybank_password';
GRANT ALL PRIVILEGES ON DATABASE mybank TO mybank_user;

\q
```

### 3.2 Настройка доступа

Отредактируйте `C:\Program Files\PostgreSQL\15\data\pg_hba.conf`:

```
# Добавьте эту строку
host    all             all             0.0.0.0/0               md5
```

Перезапустите PostgreSQL:

```powershell
Restart-Service postgresql-x64-15
```

---

## 🐍 Шаг 4: Настройка Backend (FastAPI)

### 4.1 Установка зависимостей

```powershell
cd C:\Projects\VTB_API_HACK\backend

# Создаем виртуальное окружение
python -m venv venv

# Активируем
.\venv\Scripts\activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.2 Создание .env файла

Создайте `C:\Projects\VTB_API_HACK\backend\.env`:

```env
# Database
DATABASE_URL=postgresql://financehub_user:financehub_password@localhost:5432/financehub

# Security
SECRET_KEY=super-secret-key-for-production-change-me
ENCRYPTION_KEY=32-char-encryption-key-change-me!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# VTB API
VTB_API_BASE_URL=https://ift.rtuitlab.dev
VTB_TEAM_ID=team075
VTB_TEAM_SECRET=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di

# GOST Configuration
USE_GOST=false
GOST_API_URL=https://api.gost.bankingapi.ru:8443
BANKING_API_URL=https://api.bankingapi.ru
AUTH_API_URL=https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token

# MyBank
MYBANK_API_URL=http://localhost:8001

# App
APP_NAME=FinanceHub
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
```

### 4.3 Применение миграций

```powershell
cd C:\Projects\VTB_API_HACK\backend
.\venv\Scripts\activate

# Применяем миграции
alembic upgrade head

# Заполняем тестовыми данными (опционально)
python scripts/seed_demo_data.py
```

### 4.4 Настройка PM2 для Backend

Создайте `C:\Projects\VTB_API_HACK\ecosystem.config.js`:

```javascript
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
        NODE_ENV: 'production',
      },
    },
  ],
};
```

Запуск Backend через PM2:

```powershell
cd C:\Projects\VTB_API_HACK
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## 🎨 Шаг 5: Настройка Frontend (React + Vite)

### 5.1 Установка зависимостей

```powershell
cd C:\Projects\VTB_API_HACK\frontend
npm install
```

### 5.2 Создание .env файла

Создайте `C:\Projects\VTB_API_HACK\frontend\.env.production`:

```env
VITE_API_URL=http://vtb.gistrec.cloud/api/v1
```

### 5.3 Сборка production билда

```powershell
cd C:\Projects\VTB_API_HACK\frontend
npm run build
```

Результат сборки будет в `C:\Projects\VTB_API_HACK\frontend\dist`

---

## 🔐 Шаг 6: Настройка GOST Service (опционально)

### 6.1 Требования

- CryptoPro CSP 5.0+
- Сертификат "VTB Test User"

### 6.2 Установка CryptoPro

1. Скачайте CryptoPro CSP с https://www.cryptopro.ru/products/csp/downloads
2. Установите с параметрами по умолчанию
3. Импортируйте сертификат "VTB Test User" в хранилище "Личное"

### 6.3 Проверка сертификата

```powershell
& "C:\Program Files\Crypto Pro\CSP\csptest.exe" -keyset -enum_cont -verifycontext -fqcn
```

### 6.4 Запуск GOST Service через PM2

Добавьте в `ecosystem.config.js`:

```javascript
{
  name: 'financehub-gost',
  script: 'C:\\Projects\\VTB_API_HACK\\gost_windows_service.py',
  interpreter: 'python',
  cwd: 'C:\\Projects\\VTB_API_HACK',
  instances: 1,
  autorestart: true,
  watch: false,
}
```

Запуск:

```powershell
cd C:\Projects\VTB_API_HACK
pm2 restart ecosystem.config.js
pm2 save
```

---

## 🌐 Шаг 7: Настройка Nginx Reverse Proxy

### 7.1 Конфигурация Nginx

Создайте `C:\tools\nginx-1.24.0\conf\nginx.conf`:

```nginx
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    # Логирование
    access_log  logs/access.log;
    error_log   logs/error.log;

    # Gzip сжатие
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Upstream для backend
    upstream backend {
        server 127.0.0.1:8000;
    }

    # Основной сервер
    server {
        listen       80;
        server_name  vtb.gistrec.cloud;

        # Увеличиваем лимиты
        client_max_body_size 10M;

        # Frontend (статические файлы)
        location / {
            root   C:/Projects/VTB_API_HACK/frontend/dist;
            index  index.html;
            try_files $uri $uri/ /index.html;
        }

        # Backend API
        location /api {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 300s;
            proxy_connect_timeout 300s;
        }

        # Swagger Docs
        location /docs {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # OpenAPI JSON
        location /openapi.json {
            proxy_pass http://backend;
            proxy_set_header Host $host;
        }
    }
}
```

### 7.2 Тестирование конфигурации

```powershell
cd C:\tools\nginx-1.24.0
.\nginx.exe -t
```

### 7.3 Запуск Nginx

```powershell
# Запуск
cd C:\tools\nginx-1.24.0
Start-Process nginx.exe

# Или установить как Windows Service
sc.exe create nginx binPath= "C:\tools\nginx-1.24.0\nginx.exe" start= auto
sc.exe start nginx
```

---

## 🔥 Шаг 8: Настройка Windows Firewall

### 8.1 Открыть необходимые порты

```powershell
# HTTP (80)
New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow

# HTTPS (443) - на будущее
New-NetFirewallRule -DisplayName "Allow HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow

# Backend (8000) - для отладки
New-NetFirewallRule -DisplayName "Allow Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# PostgreSQL (5432) - опционально, для внешних подключений
# New-NetFirewallRule -DisplayName "Allow PostgreSQL" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Allow
```

### 8.2 Проверка правил

```powershell
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Allow HTTP*"}
```

---

## 🚀 Шаг 9: Запуск всех сервисов

### 9.1 Полный скрипт запуска

Создайте `C:\Projects\VTB_API_HACK\start-all.ps1`:

```powershell
# Запуск всех сервисов FinanceHub

Write-Host "🚀 Starting FinanceHub on Windows Server 2025..." -ForegroundColor Green

# 1. PostgreSQL
Write-Host "📦 Starting PostgreSQL..." -ForegroundColor Cyan
Restart-Service postgresql-x64-15
Start-Sleep -Seconds 3

# 2. Backend (через PM2)
Write-Host "🐍 Starting Backend..." -ForegroundColor Cyan
cd C:\Projects\VTB_API_HACK
pm2 restart financehub-backend
Start-Sleep -Seconds 5

# 3. GOST Service (если настроен)
# Write-Host "🔐 Starting GOST Service..." -ForegroundColor Cyan
# pm2 restart financehub-gost
# Start-Sleep -Seconds 3

# 4. Nginx
Write-Host "🌐 Starting Nginx..." -ForegroundColor Cyan
cd C:\tools\nginx-1.24.0
Start-Process nginx.exe
Start-Sleep -Seconds 2

# 5. Проверка статуса
Write-Host "`n✅ All services started!" -ForegroundColor Green
Write-Host "`n📊 Status:" -ForegroundColor Yellow
pm2 status

Write-Host "`n🌍 Access URLs:" -ForegroundColor Yellow
Write-Host "   Frontend: http://vtb.gistrec.cloud"
Write-Host "   Backend API: http://vtb.gistrec.cloud/api/v1"
Write-Host "   API Docs: http://vtb.gistrec.cloud/docs"

Write-Host "`n🔑 Test credentials:" -ForegroundColor Yellow
Write-Host "   Email: team075-6@test.com"
Write-Host "   Password: password123"

Write-Host "`n✨ Done!" -ForegroundColor Green
```

### 9.2 Запуск

```powershell
cd C:\Projects\VTB_API_HACK
.\start-all.ps1
```

---

## 🧪 Шаг 10: Проверка работоспособности

### 10.1 Проверка Backend API

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET
```

### 10.2 Проверка Frontend

```powershell
Invoke-WebRequest -Uri "http://vtb.gistrec.cloud" -Method GET
```

### 10.3 Проверка через браузер

Откройте в браузере:
- Frontend: http://vtb.gistrec.cloud
- API Docs: http://vtb.gistrec.cloud/docs

---

## 🔄 Обновление приложения

### Скрипт для обновления

Создайте `C:\Projects\VTB_API_HACK\update.ps1`:

```powershell
# Обновление FinanceHub

Write-Host "🔄 Updating FinanceHub..." -ForegroundColor Green

# 1. Останавливаем сервисы
Write-Host "⏸️ Stopping services..." -ForegroundColor Cyan
pm2 stop all
cd C:\tools\nginx-1.24.0
.\nginx.exe -s stop

# 2. Обновляем код
Write-Host "📥 Pulling latest code..." -ForegroundColor Cyan
cd C:\Projects\VTB_API_HACK
git pull origin main

# 3. Backend: обновляем зависимости и миграции
Write-Host "🐍 Updating Backend..." -ForegroundColor Cyan
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
deactivate

# 4. Frontend: пересобираем
Write-Host "🎨 Rebuilding Frontend..." -ForegroundColor Cyan
cd ..\frontend
npm install
npm run build

# 5. Запускаем сервисы
Write-Host "🚀 Starting services..." -ForegroundColor Cyan
cd ..
.\start-all.ps1

Write-Host "`n✅ Update complete!" -ForegroundColor Green
```

---

## 📊 Мониторинг и логи

### PM2 команды

```powershell
# Статус всех процессов
pm2 status

# Логи backend
pm2 logs financehub-backend

# Перезапуск backend
pm2 restart financehub-backend

# Остановка backend
pm2 stop financehub-backend

# Удаление процесса
pm2 delete financehub-backend
```

### Nginx логи

```powershell
# Access log
Get-Content C:\tools\nginx-1.24.0\logs\access.log -Tail 50

# Error log
Get-Content C:\tools\nginx-1.24.0\logs\error.log -Tail 50
```

### PostgreSQL логи

```powershell
Get-Content "C:\Program Files\PostgreSQL\15\data\log\*.log" -Tail 50
```

---

## 🐛 Troubleshooting

### Backend не запускается

```powershell
# Проверяем логи PM2
pm2 logs financehub-backend --lines 100

# Проверяем подключение к PostgreSQL
psql -U financehub_user -d financehub -h localhost

# Проверяем порт 8000
netstat -ano | findstr :8000
```

### Nginx не запускается

```powershell
# Проверяем конфигурацию
cd C:\tools\nginx-1.24.0
.\nginx.exe -t

# Проверяем порт 80
netstat -ano | findstr :80
```

### Frontend показывает 404

```powershell
# Проверяем, что файлы собраны
ls C:\Projects\VTB_API_HACK\frontend\dist

# Пересобираем frontend
cd C:\Projects\VTB_API_HACK\frontend
npm run build
```

---

## 🎯 Быстрая установка (одной командой)

Создайте `C:\Projects\install.ps1`:

```powershell
# Быстрая установка FinanceHub на Windows Server

$ErrorActionPreference = "Stop"

Write-Host "🚀 FinanceHub Quick Install for Windows Server 2025" -ForegroundColor Green
Write-Host "====================================================`n" -ForegroundColor Green

# 1. Установка Chocolatey
Write-Host "📦 Installing Chocolatey..." -ForegroundColor Cyan
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 2. Установка необходимого ПО
Write-Host "📦 Installing required software..." -ForegroundColor Cyan
choco install git python311 nodejs-lts postgresql15 nginx -y --params '/Password:financehub_password'
npm install -g pm2
refreshenv

# 3. Клонирование репозитория
Write-Host "📥 Cloning repository..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path "C:\Projects" -Force
cd C:\Projects
git clone https://github.com/Hmmir/VTB_API_HACK.git
cd VTB_API_HACK

# 4. Настройка PostgreSQL
Write-Host "🗄️ Setting up PostgreSQL..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
& psql -U postgres -c "CREATE DATABASE financehub;"
& psql -U postgres -c "CREATE USER financehub_user WITH PASSWORD 'financehub_password';"
& psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE financehub TO financehub_user;"

# 5. Настройка Backend
Write-Host "🐍 Setting up Backend..." -ForegroundColor Cyan
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
deactivate

# 6. Настройка Frontend
Write-Host "🎨 Setting up Frontend..." -ForegroundColor Cyan
cd ..\frontend
npm install
npm run build

# 7. Запуск сервисов
Write-Host "🚀 Starting services..." -ForegroundColor Cyan
cd ..
pm2 start ecosystem.config.js
pm2 save
cd C:\tools\nginx-1.24.0
Start-Process nginx.exe

Write-Host "`n✅ Installation complete!" -ForegroundColor Green
Write-Host "`n🌍 Access: http://vtb.gistrec.cloud" -ForegroundColor Yellow
Write-Host "🔑 Login: team075-6@test.com / password123" -ForegroundColor Yellow
```

---

## 📞 Поддержка

- **GitHub**: https://github.com/Hmmir/VTB_API_HACK
- **Issues**: https://github.com/Hmmir/VTB_API_HACK/issues
- **Telegram**: @Hmmmir

---

## ✅ Чеклист для проверки

- [ ] PostgreSQL запущен и доступен
- [ ] Backend отвечает на http://localhost:8000/docs
- [ ] Frontend собран в /frontend/dist
- [ ] Nginx запущен и слушает порт 80
- [ ] PM2 показывает статус "online" для backend
- [ ] Файрвол разрешает порт 80
- [ ] Домен vtb.gistrec.cloud резолвится на сервер
- [ ] Приложение открывается в браузере

---

**Готово к продакшену! 🚀**

