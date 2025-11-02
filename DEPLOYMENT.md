# 🚀 Инструкция по развертыванию FinanceHub

## Предварительные требования

- Docker & Docker Compose
- Git
- Доступ к VTB Open Banking API (Team ID и Secret)

## Быстрое развертывание

### 1. Клонируйте репозиторий

```bash
git clone <repository-url>
cd "VTB API"
```

### 2. Настройте переменные окружения

**Backend (backend/.env):**

```bash
# Database
DATABASE_URL=postgresql://financehub:financehub_password@postgres:5432/financehub
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# VTB API
VTB_API_BASE_URL=https://ift.rtuitlab.dev
VTB_TEAM_ID=team010-1
VTB_TEAM_SECRET=your-vtb-secret-here
VTB_OAUTH_CALLBACK=http://localhost:3000/callback

# Encryption
ENCRYPTION_KEY=your-fernet-key-here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Frontend (frontend/.env):**

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_OAUTH_CALLBACK_URL=http://localhost:3000/callback
```

### 3. Генерация ключей

```bash
# SECRET_KEY
openssl rand -hex 32

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Запуск с Docker Compose

```bash
# Запустить все сервисы
docker-compose up -d

# Применить миграции БД
docker-compose exec backend alembic upgrade head

# Заполнить демо-данные
docker-compose exec backend python scripts/seed_demo_data.py
```

### 5. Проверка работы

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Ручное развертывание (без Docker)

### Backend

```bash
cd backend

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Настроить .env
cp .env.example .env
# Отредактировать .env с вашими credentials

# Запустить PostgreSQL и Redis
# (должны быть установлены и запущены отдельно)

# Применить миграции
alembic upgrade head

# Заполнить демо-данные
python scripts/seed_demo_data.py

# Запустить сервер
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Настроить .env
cp .env.example .env

# Запустить dev сервер
npm run dev
```

## Тестирование

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

## Production Build

### Backend

```bash
cd backend

# Установить зависимости
pip install -r requirements.txt

# Запустить с gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend

```bash
cd frontend

# Build для production
npm run build

# Preview production build
npm run preview
```

## Troubleshooting

### Проблемы с подключением к БД

```bash
# Проверить статус контейнеров
docker-compose ps

# Перезапустить PostgreSQL
docker-compose restart postgres

# Посмотреть логи
docker-compose logs postgres
```

### Проблемы с миграциями

```bash
# Откатить последнюю миграцию
docker-compose exec backend alembic downgrade -1

# Применить все миграции
docker-compose exec backend alembic upgrade head

# Создать новую миграцию
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Очистка и перезапуск

```bash
# Остановить и удалить контейнеры
docker-compose down

# Удалить volumes (ВНИМАНИЕ: удалит все данные!)
docker-compose down -v

# Пересобрать и запустить
docker-compose up -d --build
```

## Мониторинг

### Логи

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Статус

```bash
# Проверить статус
docker-compose ps

# Проверить health-check
curl http://localhost:8000/health
```

## Безопасность

1. **Никогда не коммитьте .env файлы**
2. **Используйте сильные пароли и ключи**
3. **Регулярно обновляйте зависимости**
4. **В production используйте HTTPS**
5. **Настройте rate limiting**
6. **Используйте секреты для CI/CD**

## Поддержка

Для вопросов и предложений создавайте issues в репозитории.

---

**Успешного развертывания! 🚀**

