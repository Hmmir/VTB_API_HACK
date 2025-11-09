# 🚀 Инструкция для деплоя на удаленном сервере

## 📋 Данные сервера
```
IP:       178.20.42.63
Login:    Administrator
Password: 2:5w35V-kJtYj+Bu45U9
Domain:   vtb.gistrec.cloud
OS:       Windows Server 2025
CPU:      2 cores
RAM:      4 GB
```

---

## ⚡ БЫСТРЫЙ ДЕПЛОЙ (3 шага)

### Шаг 1: Подключитесь к серверу
1. Откройте **Remote Desktop Connection** (Win+R → `mstsc`)
2. Введите: `178.20.42.63`
3. Логин: `Administrator`
4. Пароль: `2:5w35V-kJtYj+Bu45U9`

### Шаг 2: Скачайте скрипт
На сервере откройте **PowerShell от Администратора** и выполните:

```powershell
# Скачиваем скрипт деплоя
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Hmmir/VTB_API_HACK/main/DEPLOY_NOW.ps1" -OutFile "C:\DEPLOY_NOW.ps1"

# Или если не работает, клонируем весь репозиторий
New-Item -ItemType Directory -Path "C:\Projects" -Force
cd C:\Projects
git clone https://github.com/Hmmir/VTB_API_HACK.git
cd VTB_API_HACK
```

### Шаг 3: Запустите деплой
```powershell
# Если скачали только скрипт:
cd C:\
.\DEPLOY_NOW.ps1

# Если склонировали репозиторий:
cd C:\Projects\VTB_API_HACK
.\DEPLOY_NOW.ps1
```

**Ждите 10-15 минут. Скрипт сделает все автоматически!**

---

## ✅ После установки

### Проверьте статус:
```powershell
pm2 status
```

Должно быть:
```
┌─────┬───────────────────────┬─────────┬─────────┐
│ id  │ name                  │ status  │ restart │
├─────┼───────────────────────┼─────────┼─────────┤
│ 0   │ financehub-backend    │ online  │ 0       │
│ 1   │ financehub-frontend   │ online  │ 0       │
└─────┴───────────────────────┴─────────┴─────────┘
```

### Откройте приложение:
- Frontend: http://vtb.gistrec.cloud:3000
- Backend API: http://vtb.gistrec.cloud:8000
- API Docs: http://vtb.gistrec.cloud:8000/docs

### Войдите:
```
Email: team075-6@test.com
Password: password123
```

---

## 🔧 Управление

### Просмотр логов:
```powershell
# Backend
pm2 logs financehub-backend

# Frontend
pm2 logs financehub-frontend

# Все вместе
pm2 logs
```

### Перезапуск:
```powershell
# Все сервисы
pm2 restart all

# Только backend
pm2 restart financehub-backend

# Только frontend
pm2 restart financehub-frontend
```

### Остановка:
```powershell
pm2 stop all
```

### Обновление кода:
```powershell
cd C:\Projects\VTB_API_HACK
git pull origin main

# Backend
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
deactivate

# Frontend
cd ..\frontend
npm install
npm run build

# Перезапуск
cd ..
pm2 restart all
```

---

## 🐛 Если что-то не работает

### Backend не запускается:
```powershell
# Проверьте логи
pm2 logs financehub-backend --lines 50

# Проверьте PostgreSQL
Restart-Service postgresql-x64-15

# Проверьте порт
netstat -ano | findstr :8000
```

### Frontend не открывается:
```powershell
# Пересоберите
cd C:\Projects\VTB_API_HACK\frontend
npm run build

# Перезапустите
pm2 restart financehub-frontend
```

### Firewall блокирует:
```powershell
# Откройте порты вручную
New-NetFirewallRule -DisplayName "Allow Port 3000" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow
New-NetFirewallRule -DisplayName "Allow Port 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

---

## 📞 Помощь

- **Telegram**: @Hmmmir
- **GitHub Issues**: https://github.com/Hmmir/VTB_API_HACK/issues

---

## ✅ Чеклист

- [ ] Подключился по RDP
- [ ] Скачал/клонировал проект
- [ ] Запустил `DEPLOY_NOW.ps1`
- [ ] Дождался окончания установки (10-15 мин)
- [ ] `pm2 status` показывает оба сервиса `online`
- [ ] Открыл http://vtb.gistrec.cloud:3000
- [ ] Вошел с тестовым аккаунтом
- [ ] Приложение работает!

---

**ГОТОВО! Записывайте демо! 🎥**

