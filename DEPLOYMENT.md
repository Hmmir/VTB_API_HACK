# 🚀 Инструкция по развертыванию FinanceHub

## 📋 Содержание
- [Быстрый старт (Docker)](#быстрый-старт-docker)
- [Локальная разработка](#локальная-разработка)
- [Production деплой](#production-деплой)
- [GOST интеграция](#gost-интеграция)

---

## ⚡ Быстрый старт (Docker)

### Требования
- Docker Desktop (Windows/Mac) или Docker Engine (Linux)
- Docker Compose v2.0+
- 4GB RAM минимум

### Запуск за 3 команды

```bash
# 1. Клонируем репозиторий
git clone https://github.com/Hmmir/VTB_API_HACK.git
cd VTB_API_HACK

# 2. Запускаем все сервисы
docker-compose up -d

# 3. Ждем инициализации (30-60 сек)
docker-compose logs -f backend
```

### Доступ к приложению
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Тестовый пользователь
```
Email: team075-6@test.com
Password: password123
```

---

## 🛠️ Локальная разработка

### Backend (FastAPI + PostgreSQL)

```bash
cd backend

# Создаем виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Устанавливаем зависимости
pip install -r requirements.txt

# Настраиваем .env
cp .env.example .env

# Запускаем PostgreSQL
docker-compose up -d postgres

# Применяем миграции
alembic upgrade head

# Заполняем тестовыми данными
python scripts/seed_demo_data.py

# Запускаем сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React + Vite + TypeScript)

```bash
cd frontend

# Устанавливаем зависимости
npm install

# Запускаем dev-сервер
npm run dev

# Или собираем production build
npm run build
npm run preview
```

---

## 🌐 Production деплой

### Вариант 1: Docker Compose на сервере

```bash
# На сервере
git clone https://github.com/Hmmir/VTB_API_HACK.git
cd VTB_API_HACK

# Создаем production .env
cat > .env << EOF
DATABASE_URL=postgresql://user:password@postgres:5432/financehub
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=production
EOF

# Запускаем
docker-compose -f docker-compose.yml up -d

# Настраиваем nginx reverse proxy
sudo nano /etc/nginx/sites-available/financehub
```

### Nginx конфигурация

```nginx
server {
    listen 80;
    server_name vtb.gistrec.cloud;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL сертификат (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d vtb.gistrec.cloud
```

---

## 🔐 GOST интеграция

### ⚠️ Требования
- **Только Windows**
- CryptoPro CSP 5.0+
- Сертификат "VTB Test User"
- Python 3.9+

### Установка

```bash
# 1. Устанавливаем CryptoPro CSP
# Скачать: https://www.cryptopro.ru/products/csp/downloads

# 2. Устанавливаем сертификат
# Импортируем сертификат в хранилище "Личное"

# 3. Проверяем сертификат
& "C:\Program Files\Crypto Pro\CSP\csptest.exe" -keyset -enum_cont -verifycontext -fqcn

# 4. Запускаем GOST Windows Service
python gost_windows_service.py
```

### Конфигурация

Создайте `backend/.env`:

```env
GOST_CLIENT_ID=team075
GOST_CLIENT_SECRET=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di
GOST_CERT_NAME=VTB Test User
GOST_CSPTEST_PATH=C:\Program Files\Crypto Pro\CSP\csptest.exe
```

### Проверка работы

```bash
# Тест подключения
& "C:\Program Files\Crypto Pro\CSP\csptest.exe" -tlsc -server api.gost.bankingapi.ru -port 8443 -exchange 3 -user "VTB Test User" -proto 6 -verbose
```

**Ожидаемый результат:**
```
Handshake was successful
Protocol: TLS 1.2
CipherSuite: TLS_GOSTR341112_256_WITH_KUZNYECHIK_CTR_OMAC
```

### Архитектура GOST

```
Frontend (React)
    ↓ HTTP
Backend (Docker)
    ↓ HTTP (host.docker.internal:5555)
GOST Windows Service (Flask)
    ↓ Subprocess
csptest.exe (CryptoPro CSP)
    ↓ TLS 1.2 + GOST
api.gost.bankingapi.ru:8443
```

---

## 🔧 Переменные окружения

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/financehub

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Banking API
VTB_API_BASE_URL=https://hackathon.vtb.ru/openbanking/v1.0
VTB_CLIENT_ID=team075
VTB_CLIENT_SECRET=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di

# MyBank (Internal)
DEFAULT_MYBANK_PASSWORD=mybank_secure_password_2024

# GOST (Windows only)
GOST_CLIENT_ID=team075
GOST_CLIENT_SECRET=1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di
GOST_CERT_NAME=VTB Test User
GOST_CSPTEST_PATH=C:\Program Files\Crypto Pro\CSP\csptest.exe

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 📦 Структура проекта

```
VTB_API_HACK/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── integrations/ # External APIs
│   ├── alembic/          # Database migrations
│   ├── scripts/          # Utility scripts
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   ├── public/           # Static assets
│   └── package.json
├── docker-compose.yml
├── gost_windows_service.py  # GOST bridge (Windows only)
└── README.md
```

---

## 🐛 Troubleshooting

### Backend не запускается

```bash
# Проверяем логи
docker-compose logs backend

# Пересоздаем контейнер
docker-compose down
docker-compose up -d --build backend
```

### Frontend не подключается к Backend

```bash
# Проверяем CORS настройки в backend/app/main.py
# Должно быть:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### GOST не работает

1. **Проверьте CryptoPro CSP:**
   ```bash
   & "C:\Program Files\Crypto Pro\CSP\csptest.exe" -keyset -enum_cont -verifycontext -fqcn
   ```

2. **Проверьте сертификат:**
   ```bash
   certmgr.msc
   # Личное → Сертификаты → "VTB Test User"
   ```

3. **Проверьте Windows Service:**
   ```bash
   # Должен быть запущен на порту 5555
   netstat -ano | findstr :5555
   ```

---

## 📞 Поддержка

- **GitHub Issues**: https://github.com/Hmmir/VTB_API_HACK/issues
- **Документация API**: http://localhost:8000/docs
- **Hackathon**: VTB API Hackathon 2025

---

## 📄 Лицензия

MIT License - см. LICENSE файл

