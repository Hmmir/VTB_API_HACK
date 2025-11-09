# ⚡ Быстрый старт на Windows Server 2025

## 🎯 Цель
Развернуть FinanceHub на сервере `vtb.gistrec.cloud` за 15 минут.

---

## 📦 Шаг 1: Подключение к серверу

1. Откройте **Remote Desktop Connection** (mstsc.exe)
2. Введите:
   - **Computer**: `178.20.42.63`
   - **Username**: `Administrator`
   - **Password**: `2:5w35V-kJtYj+Bu45U9`
3. Нажмите **Connect**

---

## 🚀 Шаг 2: Автоматическая установка

Откройте **PowerShell от имени Администратора**:

### Вариант А: Полная автоматическая установка

```powershell
# 1. Перейдите в директорию
cd C:\Projects\VTB_API_HACK

# 2. Запустите установку
.\install.ps1

# 3. Ждите 10-15 минут
# Скрипт установит все автоматически:
# - Git, Python, Node.js, PostgreSQL, Nginx
# - Настроит базу данных
# - Соберет Frontend
# - Запустит все сервисы
```

### Вариант Б: Быстрая ручная установка

```powershell
# 1. Установите Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 2. Установите все зависимости (5 мин)
choco install git python311 nodejs-lts postgresql15 nginx -y
npm install -g pm2

# 3. Перезагрузите PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")

# 4. Склонируйте репозиторий
cd C:\Projects
git clone https://github.com/Hmmir/VTB_API_HACK.git
cd VTB_API_HACK

# 5. Настройте PostgreSQL (1 мин)
$sql = @"
CREATE DATABASE financehub;
CREATE USER financehub_user WITH PASSWORD 'financehub_password';
GRANT ALL PRIVILEGES ON DATABASE financehub TO financehub_user;
"@
$sql | & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres

# 6. Настройте Backend (3 мин)
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
deactivate

# 7. Настройте Frontend (3 мин)
cd ..\frontend
npm install
npm run build

# 8. Запустите все сервисы (1 мин)
cd ..
.\start-all.ps1
```

---

## ✅ Шаг 3: Проверка

### 3.1 Откройте в браузере
```
http://vtb.gistrec.cloud
```

### 3.2 Войдите в систему
```
Email:    team075-6@test.com
Password: password123
```

### 3.3 Проверьте API Docs
```
http://vtb.gistrec.cloud/docs
```

---

## 📊 Шаг 4: Проверка статуса

```powershell
# Статус всех процессов
pm2 status

# Логи backend
pm2 logs financehub-backend

# Проверка портов
netstat -ano | findstr ":80 :8000"
```

Ожидаемый результат:
- ✅ `financehub-backend` - online
- ✅ Nginx слушает порт 80
- ✅ Backend слушает порт 8000

---

## 🔧 Управление сервисами

### Запуск всех сервисов
```powershell
cd C:\Projects\VTB_API_HACK
.\start-all.ps1
```

### Остановка всех сервисов
```powershell
cd C:\Projects\VTB_API_HACK
.\stop-all.ps1
```

### Обновление приложения
```powershell
cd C:\Projects\VTB_API_HACK
.\update.ps1
```

### Просмотр логов
```powershell
# Backend логи
pm2 logs financehub-backend

# Nginx логи
Get-Content C:\tools\nginx-1.24.0\logs\access.log -Tail 50
```

---

## 🐛 Быстрое решение проблем

### Backend не запускается
```powershell
# Проверьте PostgreSQL
Restart-Service postgresql-x64-15

# Перезапустите backend
pm2 restart financehub-backend

# Проверьте логи
pm2 logs financehub-backend --lines 100
```

### Frontend не открывается
```powershell
# Пересоберите frontend
cd C:\Projects\VTB_API_HACK\frontend
npm run build

# Перезапустите Nginx
cd C:\tools\nginx-1.24.0
.\nginx.exe -s reload
```

### 502 Bad Gateway
```powershell
# Backend скорее всего не запущен
pm2 restart financehub-backend

# Проверьте, что backend работает
Invoke-WebRequest -Uri "http://localhost:8000/docs"
```

---

## 📱 Доступы

### Приложение
- **URL**: http://vtb.gistrec.cloud
- **Login**: team075-6@test.com
- **Password**: password123

### API
- **Docs**: http://vtb.gistrec.cloud/docs
- **OpenAPI**: http://vtb.gistrec.cloud/openapi.json

### Сервер
- **IP**: 178.20.42.63
- **Login**: Administrator
- **Password**: 2:5w35V-kJtYj+Bu45U9

---

## 📞 Помощь

- **Telegram**: @Hmmmir
- **GitHub**: https://github.com/Hmmir/VTB_API_HACK
- **Issues**: https://github.com/Hmmir/VTB_API_HACK/issues

---

## 🎯 Чеклист готовности

- [ ] Подключился к серверу по RDP
- [ ] Запустил `.\install.ps1` или прошел ручную установку
- [ ] Открыл http://vtb.gistrec.cloud в браузере
- [ ] Вошел в систему с тестовым аккаунтом
- [ ] Dashboard отображается корректно
- [ ] API Docs открываются
- [ ] `pm2 status` показывает `online`

---

**Готово! 🎉**

Приложение развернуто и готово к использованию на **vtb.gistrec.cloud**

