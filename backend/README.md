# FinanceHub Backend

FastAPI backend для мультибанковского приложения FinanceHub.

## Быстрый старт

### С Docker (рекомендуется)

```bash
# Из корня проекта
docker-compose up -d

# Выполнить миграции
docker-compose exec backend alembic upgrade head
```

### Без Docker

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

# Запустить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload --port 8000
```

## API Documentation

После запуска сервера:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Структура

```
app/
├── api/          # API endpoints
├── models/       # SQLAlchemy models
├── schemas/      # Pydantic schemas
├── services/     # Business logic
├── integrations/ # External API clients
├── utils/        # Utilities
└── main.py       # FastAPI app
```

## Тесты

```bash
# Запустить все тесты
pytest

# С coverage
pytest --cov=app --cov-report=html
```

## Миграции

```bash
# Создать миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```

