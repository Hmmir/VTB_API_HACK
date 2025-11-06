# 🏦 FinanceHub - Мультибанковский агрегатор

**VTB API Hackathon 2025** | Team 075

Единый интерфейс для управления финансами из нескольких банков с поддержкой ГОСТ-шифрования.

---

## 📋 Системные требования

- **Docker** 20.10+ и **Docker Compose** 2.0+
- **Git** для клонирования репозитория
- **8 GB RAM** (минимум 4 GB)
- **10 GB свободного места** на диске
- **Порты**: 3000 (frontend), 8000 (backend), 5432 (postgres), 6379 (redis)

---

## 🚀 Быстрый старт

### Запуск проекта

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Hmmir/VTB_API_HACK.git
cd VTB_API_HACK

# 2. Запустить через Docker
docker compose up -d

# 3. Подождать 30 секунд для инициализации

# 4. Создать демо-пользователей
docker compose exec backend python scripts/create_demo_user.py
docker compose exec backend python scripts/create_gost_demo_user.py
docker compose exec backend python scripts/seed_demo_data.py
```

### Доступ к приложению

- 🌐 **Frontend**: http://localhost:3000
- 🔌 **Backend API**: http://localhost:8000
- 📚 **API Docs (Swagger)**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc

---

## 👥 Тестовые пользователи

### 1. Demo пользователь
```
Email: demo
Password: demo123
```

### 2. Team клиенты (авто-регистрация)
```
Email: team075-1 ... team075-10
Password: password
```
**Особенности:**
- Автоматическая регистрация при первом входе
- Автоматическое подключение 3 банков (Virtual, Awesome, Smart)
- Загрузка счетов и транзакций

### 3. ГОСТ демо (для жюри)
```
Email: team075-demo
Password: gost2024
```
**Особенности:**
- ГОСТ режим включен автоматически
- Использует api.gost.bankingapi.ru:8443
- Зеленый бейдж "ГОСТ ЦБ РФ" на дашборде

---

## 👨‍👩‍👧 Family Banking Hub

Расширение мультибанка до семейного уровня: совместные бюджеты, лимиты, переводы и цели.

**Возможности:**
- Создание семейных групп, приглашения по ссылке/коду
- Общие бюджеты и контроль превышения лимитов участников (еженедельные и ежемесячные)
- Совместные цели с краудфандингом, вкладом каждого участника и прогресс-баром
- Внутрисемейные переводы с подтверждением администратора и автоматическими уведомлениями
- Настройка приватности счетов, мониторинг лимитов в фоне и интеграция с push/email уведомлениями

**Основные эндпоинты:**

```bash
# Создать семейную группу
curl -X POST http://localhost:8000/api/v1/family/groups \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Семья", "description": "Демо семья"}'

# Присоединиться по коду приглашения
curl -X POST http://localhost:8000/api/v1/family/groups/join \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"invite_code": "DEMOTEAM"}'

# Создать семейный бюджет
curl -X POST http://localhost:8000/api/v1/family/groups/1/budgets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Продукты", "amount": 50000, "period": "monthly"}'

# Создать перевод между участниками
curl -X POST http://localhost:8000/api/v1/family/groups/1/transfers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_member_id": 2, "amount": 3000, "description": "Карманные деньги"}'
```

Фронтенд доступен по маршруту `/family` (навигация → «Семья»). Панель включает вкладки: участники, бюджеты, цели, переводы и уведомления в одном окне.

---

## 📡 API Endpoints

### Authentication API

#### POST /api/v1/auth/login
Авторизация пользователя

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo",
    "password": "demo123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### POST /api/v1/auth/register
Регистрация нового пользователя

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "full_name": "John Doe"
  }'
```

#### GET /api/v1/auth/me
Получить информацию о текущем пользователе

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": 1,
  "email": "demo@financehub.ru",
  "full_name": "Demo User",
  "use_gost_mode": false
}
```

---

### Banks API

#### GET /api/v1/banks/available-banks
Список доступных банков

**Request:**
```bash
curl http://localhost:8000/api/v1/banks/available-banks
```

**Response:**
```json
[
  {
    "code": "vbank",
    "name": "Virtual Bank",
    "icon": "💜",
    "description": "Виртуальный банк для тестирования"
  },
  {
    "code": "abank",
    "name": "Awesome Bank",
    "icon": "🟢"
  },
  {
    "code": "sbank",
    "name": "Smart Bank",
    "icon": "🔵"
  }
]
```

#### POST /api/v1/banks/connect-demo
Подключить банк (демо режим)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/banks/connect-demo \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bank_code": "vbank",
    "client_number": "1"
  }'
```

#### GET /api/v1/banks/connections
Список подключенных банков

**Request:**
```bash
curl http://localhost:8000/api/v1/banks/connections \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "bank_code": "vbank",
    "bank_name": "Virtual Bank",
    "status": "ACTIVE",
    "created_at": "2025-11-04T10:00:00"
  }
]
```

---

### Accounts API

#### GET /api/v1/accounts/
Получить список счетов

**Request:**
```bash
curl http://localhost:8000/api/v1/accounts/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "account_number": "40817810099910004312",
    "account_name": "Основной счет",
    "account_type": "CHECKING",
    "balance": 150000.50,
    "currency": "RUB",
    "bank_connection": {
      "bank_code": "vbank",
      "bank_name": "Virtual Bank"
    }
  }
]
```

#### GET /api/v1/accounts/{account_id}
Получить детали счета

**Request:**
```bash
curl http://localhost:8000/api/v1/accounts/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Transactions API

#### GET /api/v1/transactions/
Получить список транзакций

**Request:**
```bash
# Все транзакции
curl http://localhost:8000/api/v1/transactions/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# С фильтрами
curl "http://localhost:8000/api/v1/transactions/?limit=10&transaction_type=EXPENSE" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "account_id": 1,
    "amount": -500.00,
    "currency": "RUB",
    "transaction_type": "EXPENSE",
    "description": "Продукты",
    "merchant": "Магазин №5",
    "transaction_date": "2025-11-04T14:30:00",
    "category": {
      "id": 1,
      "name": "Продукты",
      "icon": "🛒"
    }
  }
]
```

---

### Analytics API

#### GET /api/v1/analytics/summary
Сводка по финансам за период

**Request:**
```bash
# За 30 дней
curl "http://localhost:8000/api/v1/analytics/summary?period_days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"

# За все время
curl "http://localhost:8000/api/v1/analytics/summary?period_days=365" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_income": 150000.00,
  "total_expenses": 75000.00,
  "net_balance": 75000.00,
  "transaction_count": 45
}
```

#### GET /api/v1/analytics/by-category
Расходы по категориям

**Request:**
```bash
curl "http://localhost:8000/api/v1/analytics/by-category?period_days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
[
  {
    "category_id": 1,
    "category": "Продукты",
    "total": 25000.00,
    "count": 15
  },
  {
    "category_id": 2,
    "category": "Транспорт",
    "total": 8000.00,
    "count": 8
  }
]
```

#### GET /api/v1/analytics/trends
Тренды доходов/расходов

**Request:**
```bash
curl "http://localhost:8000/api/v1/analytics/trends?period_days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Budgets API

#### GET /api/v1/budgets/
Список бюджетов

**Request:**
```bash
curl http://localhost:8000/api/v1/budgets/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### POST /api/v1/budgets/
Создать бюджет

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/budgets/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Продукты",
    "amount": 30000,
    "period": "MONTHLY",
    "category_id": 1
  }'
```

---

### Multibank Proxy API

#### GET /api/v1/unified-banking/sources
Список доступных источников данных

**Request:**
```bash
curl http://localhost:8000/api/v1/unified-banking/sources
```

**Response:**
```json
{
  "sources": [
    {
      "id": "vtb_api",
      "name": "VTB API - Песочница",
      "banks": [
        {"code": "vbank", "name": "Virtual Bank", "icon": "💜"},
        {"code": "abank", "name": "Awesome Bank", "icon": "🟢"},
        {"code": "sbank", "name": "Smart Bank", "icon": "🔵"}
      ],
      "status": "active",
      "gost_support": false
    },
    {
      "id": "banking_api",
      "name": "Banking API - Стенд организаторов",
      "status": "configured",
      "gost_support": true,
      "gost_endpoint": "https://api.gost.bankingapi.ru:8443"
    }
  ],
  "gost_info": {
    "description": "ГОСТ - это протокол криптографического шифрования, а НЕ банк!",
    "toggle": "use_gost=true parameter for Banking API calls"
  }
}
```

#### GET /api/v1/unified-banking/accounts/all
Получить счета из всех источников

**Request:**
```bash
# Без ГОСТ
curl "http://localhost:8000/api/v1/unified-banking/accounts/all?use_gost=false" \
  -H "Authorization: Bearer YOUR_TOKEN"

# С ГОСТ
curl "http://localhost:8000/api/v1/unified-banking/accounts/all?use_gost=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### GOST API

#### GET /api/v1/gost/status
Статус ГОСТ подключения

**Request:**
```bash
curl http://localhost:8000/api/v1/gost/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "enabled": true,
  "mode": "GOST",
  "api_endpoint": "https://api.gost.bankingapi.ru:8443",
  "auth_endpoint": "https://auth.bankingapi.ru",
  "description": "🔒 ГОСТ-шлюз настроен на api.gost.bankingapi.ru:8443"
}
```

#### POST /api/v1/gost/test-connection
Тестировать ГОСТ подключение

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/gost/test-connection \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🗄️ База данных

### Структура (16+ таблиц)

1. **users** - пользователи
2. **bank_connections** - подключения к банкам
3. **accounts** - счета пользователей
4. **transactions** - транзакции
5. **categories** - категории расходов
6. **budgets** - бюджеты
7. **goals** - финансовые цели
8. **recommendations** - рекомендации
9. **bank_products** - банковские продукты
10. **consents** - согласия для межбанковских операций
11. **consent_requests** - запросы на согласия
12. **payments** - платежи
13. **notifications** - уведомления
14. **key_rate_history** - история ключевой ставки ЦБ
15. **bank_capital** - капитал банков
16. **partner_banks** - партнерские банки

### Миграции

```bash
# Применить миграции
docker compose exec backend alembic upgrade head

# Создать новую миграцию
docker compose exec backend alembic revision --autogenerate -m "description"

# Откатить миграцию
docker compose exec backend alembic downgrade -1
```

---

## 🔐 Безопасность

### JWT Tokens

**Access Token (HS256):**
- Срок действия: 30 минут
- Алгоритм: HS256
- Содержит: user_id, email

**Refresh Token:**
- Срок действия: 7 дней
- Используется для обновления access token

### Шифрование данных

Токены банков хранятся в зашифрованном виде:

```python
from app.utils.security import encrypt_token, decrypt_token

encrypted = encrypt_token("sensitive_token")
decrypted = decrypt_token(encrypted)
```

### CORS

Настроено для:
- http://localhost:3000
- http://localhost:5173
- http://127.0.0.1:3000

---

## 🏗️ Архитектура

### Backend

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── auth.py       # Авторизация
│   │   ├── banks.py      # Управление банками
│   │   ├── accounts.py   # Счета
│   │   ├── transactions.py
│   │   ├── analytics.py
│   │   ├── budgets.py
│   │   ├── goals.py
│   │   ├── recommendations.py
│   │   ├── gost.py       # ГОСТ интеграция
│   │   └── unified_banking.py  # Multibank API
│   │
│   ├── models/           # SQLAlchemy модели
│   ├── services/         # Бизнес-логика
│   │   ├── auth_service.py
│   │   ├── auto_connect_service.py
│   │   └── openbanking_service.py
│   │
│   ├── integrations/     # Внешние API
│   │   ├── vtb_api.py    # VTB OpenBanking client
│   │   └── gost_client.py
│   │
│   ├── utils/           # Утилиты
│   │   ├── security.py  # JWT, encryption
│   │   └── error_handlers.py
│   │
│   ├── config.py        # Конфигурация
│   ├── database.py      # База данных
│   └── main.py          # FastAPI app
│
├── alembic/             # Миграции
├── scripts/             # Утилиты
└── tests/              # Тесты
```

### Frontend

```
frontend/
└── src/
    ├── pages/          # Страницы
    │   ├── LoginPage.tsx
    │   ├── DashboardPage.tsx
    │   ├── AccountsPage.tsx
    │   ├── TransactionsPage.tsx
    │   ├── AnalyticsPage.tsx
    │   ├── BudgetsPage.tsx
    │   ├── GoalsPage.tsx
    │   └── RecommendationsPage.tsx
    │
    ├── components/     # Компоненты
    │   ├── common/     # Общие (Button, Card, etc.)
    │   ├── charts/     # Графики (Recharts)
    │   └── accounts/   # Специфичные
    │
    ├── services/       # API клиенты
    ├── contexts/       # React Context
    ├── utils/          # Утилиты
    └── types/          # TypeScript типы
```

---

## 🎨 Технологический стек

### Backend
- **FastAPI** - современный async веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **Alembic** - миграции базы данных
- **PostgreSQL** - основная БД
- **Pydantic** - валидация данных
- **python-jose** - JWT токены
- **httpx** - async HTTP клиент
- **tenacity** - retry механизмы

### Frontend
- **React 18** - UI библиотека
- **TypeScript** - типизация
- **Vite** - сборщик
- **Tailwind CSS** - стили
- **React Router** - роутинг
- **Axios** - HTTP клиент
- **Recharts** - графики
- **React Hot Toast** - уведомления

### DevOps
- **Docker** - контейнеризация
- **Docker Compose** - оркестрация
- **Nginx** - веб-сервер (в production)

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Backend тесты
docker compose exec backend pytest

# С coverage
docker compose exec backend pytest --cov=app --cov-report=html

# Frontend тесты
docker compose exec frontend npm test
```

### Ручное тестирование через Swagger

1. Открыть http://localhost:8000/docs
2. Нажать "Authorize"
3. Получить токен через `/api/v1/auth/login`
4. Ввести токен в формате: `Bearer YOUR_TOKEN`
5. Тестировать endpoints

---

## 📊 Мониторинг

### Логи

```bash
# Все логи
docker compose logs

# Только backend
docker compose logs backend

# Только frontend
docker compose logs frontend

# Следить в реальном времени
docker compose logs -f backend
```

### Здоровье сервисов

```bash
# Статус контейнеров
docker compose ps

# Использование ресурсов
docker compose stats
```

---

## 🚀 Деплой

### Production

1. **Настроить переменные окружения**

```bash
cp .env.example .env
nano .env
```

Обязательно изменить:
- `SECRET_KEY` - случайная строка 32+ символов
- `ENCRYPTION_KEY` - 32 символа для Fernet
- `VTB_TEAM_SECRET` - ваш секрет от VTB

2. **Запустить production build**

```bash
docker compose -f docker-compose.prod.yml up -d
```

3. **Настроить Nginx**

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3000;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

4. **SSL через Let's Encrypt**

```bash
sudo certbot --nginx -d yourdomain.com
```

---

## 🔄 Обновление

```bash
# Остановить проект
docker compose down

# Обновить код
git pull

# Пересобрать
docker compose build

# Запустить
docker compose up -d

# Применить миграции
docker compose exec backend alembic upgrade head
```

---

## 🐛 Troubleshooting

### Проблема: Контейнер падает

```bash
# Проверить логи
docker compose logs backend --tail=100

# Пересоздать контейнер
docker compose up -d --force-recreate backend
```

### Проблема: База данных не инициализируется

```bash
# Удалить volumes и пересоздать
docker compose down -v
docker compose up -d
```

### Проблема: 401 Unauthorized

```bash
# Проверить токен
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Получить новый токен
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo","password":"demo123"}'
```

---

## 📚 Дополнительные документы

- `GOST_CORRECT_ARCHITECTURE.md` - Архитектура ГОСТ
- `JURY_REQUIREMENTS_CHECK.md` - Соответствие требованиям жюри
- `ALL_FIXES_AND_COMPARISON.md` - Сравнение с bank-in-a-box
- `QUICK_TEST.md` - Быстрая проверка проекта
- `PROJECT_WORKING.md` - Подробная инструкция

---

## 🔧 Troubleshooting

### Проблема: Порты заняты

```bash
# Проверить занятые порты
netstat -ano | findstr "3000 8000 5432 6379"

# Остановить контейнеры
docker-compose down

# Изменить порты в docker-compose.yml
```

### Проблема: Контейнеры не запускаются

```bash
# Очистить все контейнеры и образы
docker-compose down -v
docker system prune -a

# Пересобрать
docker-compose build --no-cache
docker-compose up -d
```

### Проблема: База данных не инициализируется

```bash
# Пересоздать базу данных
docker-compose down -v
docker volume rm vtbapi_postgres_data
docker-compose up -d

# Подождать 30 секунд и создать пользователей
docker-compose exec backend python scripts/create_demo_user.py
docker-compose exec backend python scripts/create_gost_demo_user.py
docker-compose exec backend python scripts/seed_demo_data.py
```

### Проблема: Frontend не загружается

```bash
# Очистить кэш браузера (Ctrl+Shift+Delete)
# Или открыть в режиме инкогнито (Ctrl+Shift+N)

# Пересобрать frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Проблема: Ошибки в логах backend

```bash
# Посмотреть логи
docker-compose logs backend --tail=100

# Перезапустить backend
docker-compose restart backend
```

---

## 👨‍💻 Команда

**Team 075** - VTB API Hackathon 2025

---

## 📄 Лицензия

MIT License

---

## 🎉 Благодарности

- VTB API за организацию хакатона
- OpenBanking Russia за API спецификации
- Anthropic Claude за помощь в разработке
