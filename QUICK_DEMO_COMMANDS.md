# 🎯 Quick Demo Commands - Для Демонстрации Жюри

## Подготовка (перед демонстрацией)

### 1. Запустить Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Запустить Frontend (в отдельном терминале)
```powershell
cd frontend
npm install
npm run dev
```

### 3. Проверить что всё работает
```powershell
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## Demo Commands (во время презентации)

### ШАГ 1: Проверка Аутентификации

```powershell
cd backend
$env:VTB_CLIENT_ID="team075"
$env:VTB_CLIENT_SECRET="1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
python test_jury_requirements.py
```

**Что покажет:**
- ✅ Успешное получение access_token
- ✅ Работа со стандартным API
- ⚠️ GOST требует настройки (ожидаемо)

---

### ШАГ 2: GOST Status API

```powershell
# Проверка статуса GOST
curl http://localhost:8000/api/v1/gost/status | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Список требований
curl http://localhost:8000/api/v1/gost/requirements | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Тест подключения
curl http://localhost:8000/api/v1/gost/test-connection | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

### ШАГ 3: Показать GOST Adapter Code

```powershell
# Открыть в редакторе
code backend/app/services/gost_adapter.py

# Или показать ключевые части
Get-Content backend/app/services/gost_adapter.py | Select-String -Pattern "class GOSTAdapter" -Context 0,20
```

---

### ШАГ 4: Показать Frontend с GOST Badge

```
1. Открыть http://localhost:3000
2. Залогиниться (или зарегистрироваться)
3. На Dashboard показать GOST Status Badge
4. Кликнуть "View Details" - показать требования
```

---

### ШАГ 5: Live API Documentation

```
Открыть: http://localhost:8000/docs

Показать:
- /api/v1/gost/status
- /api/v1/gost/requirements
- /api/v1/gost/test-connection
```

---

## Quick Fixes (если что-то не работает)

### Backend не запускается:
```powershell
cd backend
pip install fastapi uvicorn python-dotenv httpx pydantic sqlalchemy psycopg2-binary alembic
uvicorn app.main:app --reload --port 8000
```

### Frontend не запускается:
```powershell
cd frontend
npm install --force
npm run dev
```

### База данных не готова:
```powershell
cd backend
# Используем SQLite для демо (не нужен PostgreSQL)
$env:DATABASE_URL="sqlite:///./financehub.db"
alembic upgrade head
python scripts/seed_demo_data.py
```

---

## One-Liner Demo (если совсем мало времени)

```powershell
# Всё в одной команде
cd backend; $env:VTB_CLIENT_ID="team075"; $env:VTB_CLIENT_SECRET="1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"; python test_jury_requirements.py
```

**Показывает:**
- Аутентификацию ✅
- Стандартный API ✅  
- GOST статус ⚠️ (требует настройки)

---

## Backup Plan (если нет интернета)

### Показать оффлайн:
1. Код GOST Adapter (уже на диске)
2. Документацию (README, GOST_CLIENT_READY_SOLUTION.md)
3. Архитектурную диаграмму (нарисовать на доске)
4. Презентацию (PDF)

---

## Timing (5 минут презентации)

- **0:00-1:30** - Введение + Working MVP (показать UI)
- **1:30-2:30** - GOST Architecture (код + test_jury_requirements.py)
- **2:30-3:30** - GOST Status API (curl команды)
- **3:30-4:30** - UI Integration + Документация
- **4:30-5:00** - Коммерческое предложение + Q&A

---

## После Демонстрации

### Ссылки для жюри:
```
GitHub: https://github.com/financehub/financehub
Live Demo: https://demo.financehub.ru
Документация: docs.financehub.ru

Контакты:
Email: team075@financehub.ru
Telegram: @financehub_team075
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
```powershell
cd backend
$env:PYTHONPATH="."
python test_jury_requirements.py
```

### "Connection refused to localhost:8000"
```powershell
# Проверить запущен ли backend
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# Перезапустить
cd backend
uvicorn app.main:app --reload --port 8000
```

### "npm command not found"
```powershell
# Установить Node.js
winget install OpenJS.NodeJS

# Или использовать только backend demo
cd backend
python test_jury_requirements.py
```

---

**Готовы к демонстрации! 🚀**

*Все команды протестированы на Windows 11 PowerShell*

