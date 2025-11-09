# 🚀 СТАРТ - Деплой на vtb.gistrec.cloud

## ⚡ Самый быстрый способ (1 команда, 15 минут)

### Подключитесь к серверу:
```
RDP: 178.20.42.63
Login: Administrator
Password: 2:5w35V-kJtYj+Bu45U9
```

### Запустите в PowerShell (от Администратора):
```powershell
cd C:\Projects\VTB_API_HACK
.\install.ps1
```

### Откройте браузер:
```
http://vtb.gistrec.cloud
Login: team075-6@test.com
Password: password123
```

**Готово! ✅**

---

## 📚 Полная документация

- **[FAST_START_RU.md](FAST_START_RU.md)** - Быстрый старт с пошаговой инструкцией
- **[DEPLOY_WINDOWS_SERVER.md](DEPLOY_WINDOWS_SERVER.md)** - Полная инструкция по деплою
- **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - Чеклист для проверки всех компонентов

---

## 🛠️ Управление

```powershell
# Запуск
.\start-all.ps1

# Остановка
.\stop-all.ps1

# Обновление
.\update.ps1

# Статус
pm2 status

# Логи
pm2 logs financehub-backend
```

---

## 🎯 Что будет установлено?

1. **Chocolatey** - пакетный менеджер Windows
2. **Git** - система контроля версий
3. **Python 3.11** - для Backend
4. **Node.js 20** - для Frontend
5. **PostgreSQL 15** - база данных
6. **Nginx** - веб-сервер
7. **PM2** - менеджер процессов

---

## 📊 Архитектура

```
Internet
   ↓
vtb.gistrec.cloud:80 (Nginx)
   ↓
   ├─→ / (Frontend: React SPA)
   └─→ /api (Backend: FastAPI:8000)
         ↓
      PostgreSQL:5432
```

---

## ✅ Проверка работы

```powershell
# 1. Проверка сервисов
pm2 status
# Ожидается: financehub-backend - online

# 2. Проверка портов
netstat -ano | findstr ":80 :8000"

# 3. Проверка Backend API
Invoke-WebRequest -Uri "http://localhost:8000/docs"

# 4. Проверка Frontend
Invoke-WebRequest -Uri "http://vtb.gistrec.cloud"
```

---

## 🐛 Быстрое решение проблем

### Backend не работает
```powershell
pm2 restart financehub-backend
pm2 logs financehub-backend --lines 100
```

### Frontend не открывается
```powershell
cd C:\Projects\VTB_API_HACK\frontend
npm run build
cd C:\tools\nginx-1.24.0
.\nginx.exe -s reload
```

### PostgreSQL не доступен
```powershell
Restart-Service postgresql-x64-15
```

---

## 📞 Поддержка

- **Telegram**: @Hmmmir
- **GitHub**: https://github.com/Hmmir/VTB_API_HACK
- **Email**: support@financehub.ru

---

## 🎓 Структура файлов

```
VTB_API_HACK/
├── install.ps1                    # ⚡ Автоматическая установка
├── start-all.ps1                  # 🚀 Запуск всех сервисов
├── stop-all.ps1                   # ⏸️ Остановка всех сервисов
├── update.ps1                     # 🔄 Обновление приложения
├── ecosystem.config.js            # ⚙️ Конфигурация PM2
├── FAST_START_RU.md              # 📖 Быстрый старт
├── DEPLOY_WINDOWS_SERVER.md      # 📚 Полная документация
└── DEPLOY_CHECKLIST.md           # ✅ Чеклист проверки
```

---

**Удачи! 🚀**

