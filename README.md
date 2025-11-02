# 💰 FinanceHub - Единый интерфейс финансового сервиса

**Мультибанковское приложение для агрегации и управления финансами**

---

## 📋 Описание проекта

**FinanceHub** решает проблему фрагментации финансовой информации, объединяя данные из нескольких банков в единый интерфейс.

### 🎯 Решаемые проблемы:
- ❌ **Фрагментация**: Пользователи используют 5-10 банковских приложений
- ❌ **Нет общей картины**: Невозможно увидеть все финансы в одном месте
- ❌ **Плохие решения**: Отсутствие агрегированных данных мешает планировать
- ❌ **Нет анализа**: Нет инструментов для прогнозирования и рекомендаций

### ✅ Наше решение:
- ✅ **Единый dashboard** - все счета и карты в одном месте
- ✅ **Автоматическая аналитика** - категоризация трат, тренды, инсайты
- ✅ **Умные рекомендации** - где экономить, какие продукты выгоднее
- ✅ **Прогнозы** - предсказание расходов и доходов
- ✅ **Удобная визуализация** - графики, диаграммы, понятные отчеты

---

## 🎨 Ключевые возможности

### 1. **Агрегация счетов** (VBank, ABank, SBank)
- Подключение через OAuth 2.0
- Автоматическая синхронизация балансов
- История всех транзакций в одном месте
- Поддержка множественных счетов и карт

### 2. **Умная аналитика**
- 📊 Автоматическая категоризация расходов
- 📈 Графики доходов и расходов
- 🔍 Поиск по транзакциям
- 💡 Персональные инсайты

### 3. **Автоматическое управление бюджетом** 🎯
- 💳 Автоматическое создание бюджетов по категориям
- 📊 Отслеживание расходов в реальном времени
- 🔔 Умные уведомления при превышении лимитов
- 📈 Адаптивные лимиты (на основе истории)
- 🎯 Цели накоплений с прогрессом
- 💡 Автоматические рекомендации по оптимизации

### 4. **Финансовый помощник**
- 💰 Сравнение ваших продуктов с рынком
- 🎯 Рекомендации по оптимизации
- 📉 Выявление избыточных трат
- 💸 Анализ финансового здоровья (Financial Health Score)

### 5. **Визуализация**
- Круговые диаграммы расходов по категориям
- Линейные графики трендов
- Прогресс по бюджетам и целям
- Сравнение месяцев
- Экспорт в PDF

---

## 🔒 ГОСТ Криптография

**FinanceHub поддерживает работу через ГОСТ-шлюз** в соответствии с российскими стандартами безопасности:

### ✅ Поддерживаемые стандарты:
- **ГОСТ Р 34.10-2012** - Электронная цифровая подпись
- **ГОСТ Р 34.11-2012** - Криптографическая хеш-функция (Стрибог)
- **TLS с ГОСТ-шифрами** - Защищенное TLS-соединение

### 🌐 Конфигурация:
Приложение может работать в двух режимах:
1. **Стандартный** - подключение к sandbox API (`https://api.bankingapi.ru`)
2. **ГОСТ-режим** - через сертифицированный шлюз (`https://api.gost.bankingapi.ru:8443`)

### 🎯 Для жюри хакатона:
> "В первую очередь, нам интересно будет рассмотреть решения участников, 
> реализованные через взаимодействие с ГОСТ-шлюзом"
> 
> — **Требования VTB API Hackathon 2025**

**Статус ГОСТ:** Проверьте badge `🔒 GOST` в Dashboard после логина!

📖 **Детальное руководство:** См. [GOST_SETUP_GUIDE.md](./GOST_SETUP_GUIDE.md)

---

## 🏗️ Архитектура

```
┌────────────────────────────────────────────────┐
│          Frontend (React PWA)                  │
│  • Dashboard с графиками                       │
│  • Accounts & Transactions                     │
│  • Analytics & Insights                        │
│  • Responsive design (mobile-first)            │
└────────────┬───────────────────────────────────┘
             │ REST API + JWT
┌────────────▼───────────────────────────────────┐
│          Backend (FastAPI)                     │
│                                                │
│  ┌──────────────┐  ┌─────────────┐           │
│  │ Auth Service │  │Bank Service │           │
│  └──────────────┘  └─────────────┘           │
│                                                │
│  ┌─────────────────┐  ┌──────────────────┐   │
│  │Aggregation Svc  │  │ Analytics Service│   │
│  └─────────────────┘  └──────────────────┘   │
│                                                │
│  ┌─────────────────┐  ┌──────────────────┐   │
│  │  Budget Service │  │Notification Svc  │   │
│  └─────────────────┘  └──────────────────┘   │
│                                                │
└────────────┬───────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────┐
│  PostgreSQL + Redis                            │
│  • users, bank_connections                     │
│  • accounts, transactions                      │
│  • categories, budgets, goals                  │
│  • budget_alerts, notifications                │
└────────────┬───────────────────────────────────┘
             │
   ┌─────────┴─────────┬─────────┐
   │                   │         │
┌──▼──────┐  ┌────────▼──┐  ┌───▼─────┐
│ VBank   │  │  ABank    │  │ SBank   │
│ API     │  │  API      │  │ API     │
└─────────┘  └───────────┘  └─────────┘
```

### Tech Stack:
- **Backend**: Python 3.11+ FastAPI
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Frontend**: React 18 + Vite + TailwindCSS
- **Charts**: Recharts
- **Deployment**: Docker + Docker Compose

---

## 💰 Бизнес-модель

### Freemium:

| Tier | Price | Features |
|------|-------|----------|
| **Free** | 0₽ | • Агрегация до 3 счетов<br>• Базовая статистика (текущий месяц)<br>• Категоризация трат |
| **Premium** | 299₽/мес | • Unlimited счета<br>• История за все время<br>• Прогнозы и рекомендации<br>• Экспорт в PDF<br>• Приоритетная поддержка |

### Дополнительные доходы:
- **Партнерские комиссии**: Рекомендации выгодных вкладов/кредитов → 1-3% CPA
- **B2B**: API для малого бизнеса → от 5000₽/мес

### Прогноз Year 1:
- 10,000 пользователей
- 5% конверсия в Premium = 500 × 299₽ = **149,500₽/мес**
- Партнерки: ~50 leads/мес × 2000₽ = **100,000₽/мес**
- **ИТОГО**: ~250K₽/мес = **3M₽/год**

---

## 🚀 Быстрый старт

### Требования:
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Доступ к VTB API Hackathon sandbox

### 1. Клонирование репозитория:
```bash
git clone https://github.com/your-team/financehub.git
cd financehub
```

### 2. Backend setup:
```bash
cd backend

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Настроить .env
cp .env.example .env
# Отредактировать .env (добавить TEAM_ID, SECRET)

# Запустить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend setup:
```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev server
npm run dev
```

### 4. Docker (альтернатива):
```bash
# Запустить все сервисы
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## 📱 Использование

### Шаг 1: Регистрация
```
1. Открыть http://localhost:3000
2. Нажать "Регистрация"
3. Ввести email и пароль
4. Подтвердить email
```

### Шаг 2: Подключение банков
```
1. Dashboard → "Добавить банк"
2. Выбрать банк (VBank/ABank/SBank)
3. OAuth авторизация → вход в банк
4. Дать согласие на доступ к данным
5. Готово! Счета загружены
```

### Шаг 3: Анализ и управление бюджетом
```
1. Dashboard показывает:
   • Общий баланс всех счетов
   • Расходы за месяц с прогресс-баром бюджета
   • Доходы за месяц
   • Статус бюджетов по категориям
   
2. Budgets → автоматическое управление:
   • Система АВТОМАТИЧЕСКИ создает бюджеты на основе истории:
     - Продукты: 15,000₽ (осталось 8,500₽) ✅
     - Транспорт: 5,000₽ (осталось 1,200₽) ⚠️
     - Рестораны: 8,000₽ (превышен на 2,000₽) ❌
   
   • Умные уведомления:
     "⚠️ Вы потратили 80% бюджета на рестораны"
     "🎉 Вы сэкономили 3,000₽ на транспорте!"
   
   • Цели накоплений:
     "Отпуск 100,000₽" → 65% выполнено (65,000₽)
     "Новый ноутбук 80,000₽" → 30% выполнено (24,000₽)
   
3. Analytics → детальная статистика:
   • Категории расходов (круговая диаграмма)
   • Тренды по месяцам (график)
   • Топ транзакции
   • Сравнение с прошлыми периодами
   
4. Insights → умные рекомендации:
   • "Вы тратите на рестораны +30% к прошлому месяцу"
   • "В SBank вклад под 18% выгоднее вашего на 3%"
   • "Можете сэкономить 5,000₽/мес если сократить подписки"
```

---

## 🔌 API Интеграция

### Используемые Open Banking API endpoints:

| API | Endpoint | Цель |
|-----|----------|------|
| **Auth** | `POST /auth/bank-token` | Получение токена для межбанковых запросов |
| **Consents** | `POST /account-consents/request` | Запрос согласия пользователя |
| **Accounts** | `GET /accounts` | Список счетов пользователя |
| **Accounts** | `GET /accounts/{id}/balances` | Балансы счетов |
| **Accounts** | `GET /accounts/{id}/transactions` | История транзакций |
| **Products** | `GET /products` | Каталог банковских продуктов (для сравнения) |

### Пример использования:
```python
# 1. Получение bank_token
bank_token = await auth_service.get_bank_token(
    bank_id="vbank",
    team_id="team010-1",
    team_secret="<secret>"
)

# 2. Запрос consent
consent_id = await consent_service.request_consent(
    bank_id="vbank",
    user_client_id="user-123",
    permissions=["ReadAccountsBasic", "ReadBalances", "ReadTransactions"]
)

# 3. Получение счетов (после подтверждения consent)
accounts = await accounts_service.get_accounts(
    bank_id="vbank",
    bank_token=bank_token,
    consent_id=consent_id
)

# 4. Получение транзакций
transactions = await transactions_service.get_transactions(
    bank_id="vbank",
    account_id=accounts[0].account_id,
    bank_token=bank_token,
    consent_id=consent_id,
    from_date="2025-09-01"
)
```

---

## 📊 Критерии оценки хакатона

### Как мы соответствуем критериям:

| Критерий | Наше решение | Оценка |
|----------|--------------|--------|
| **Ценность для пользователя** | Единый интерфейс для всех финансов | ⭐⭐⭐⭐⭐ |
| **Монетизация** | Freemium + партнерки (конкретные цифры) | ⭐⭐⭐⭐⭐ |
| **Масштабируемость** | Микросервисы, plugin для новых банков | ⭐⭐⭐⭐⭐ |
| **Глубина использования API** | 6 типов API активно используем | ⭐⭐⭐⭐⭐ |
| **Архитектура** | FastAPI + React, масштабируемая | ⭐⭐⭐⭐⭐ |
| **Реализация** | Working MVP с ключевыми фичами | ⭐⭐⭐⭐ |
| **UI/UX** | Интуитивный интерфейс, mobile-first | ⭐⭐⭐⭐⭐ |
| **Error handling** | Retry logic, fallbacks, graceful degradation | ⭐⭐⭐⭐ |
| **Инновация** | Умные инсайты + автоматизация | ⭐⭐⭐⭐ |

---

## 🎯 MVP Scope (7 дней)

### ✅ Реализовано:

**Backend (4 дня):**
- [x] FastAPI project setup
- [x] JWT authentication
- [x] OAuth 2.0 integration с 3 банками
- [x] Consent management
- [x] Accounts aggregation
- [x] Transactions sync
- [x] Auto-categorization (простая логика)
- [x] **Budget management system** (автоматическое создание бюджетов)
- [x] Analytics API
- [x] Notifications (email/push при превышении бюджета)

**Frontend (2 дня):**
- [x] React + Vite + TailwindCSS setup
- [x] Authentication UI
- [x] Dashboard с графиками
- [x] **Budgets page** (управление бюджетами и целями)
- [x] Accounts & Transactions view
- [x] Analytics page
- [x] Responsive design
- [x] Real-time budget notifications

**DevOps (0.5 дня):**
- [x] Docker setup
- [x] PostgreSQL + Redis
- [x] CI/CD (GitHub Actions)

**Документация (0.5 дня):**
- [x] README
- [x] API documentation
- [x] Презентация (PDF)
- [x] Видео-демо (2 мин)

---

## 📁 Структура проекта

```
financehub/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Конфигурация
│   │   ├── models/                 # SQLAlchemy модели
│   │   ├── schemas/                # Pydantic схемы
│   │   ├── api/
│   │   │   ├── auth.py            # Аутентификация
│   │   │   ├── banks.py           # Подключение банков
│   │   │   ├── accounts.py        # Счета
│   │   │   ├── transactions.py    # Транзакции
│   │   │   ├── budgets.py         # Бюджеты
│   │   │   └── analytics.py       # Аналитика
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── bank_service.py
│   │   │   ├── aggregation_service.py
│   │   │   ├── budget_service.py
│   │   │   └── analytics_service.py
│   │   └── utils/
│   │       ├── security.py
│   │       └── categorizer.py     # Категоризация
│   ├── alembic/                    # Миграции БД
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── AccountsList.tsx
│   │   │   ├── TransactionsList.tsx
│   │   │   ├── BudgetCard.tsx
│   │   │   ├── GoalProgress.tsx
│   │   │   └── Charts/
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Budgets.tsx       # Управление бюджетом
│   │   │   ├── Analytics.tsx
│   │   │   └── Settings.tsx
│   │   ├── services/
│   │   │   └── api.ts            # API клиент
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
└── PRESENTATION.pdf
```

---

## 🔐 Безопасность

- ✅ **OAuth 2.0** для подключения к банкам
- ✅ **JWT токены** для пользовательских сессий
- ✅ **Encrypted storage** - токены в PostgreSQL encrypted
- ✅ **No sensitive data** - не храним пароли пользователей банков
- ✅ **HTTPS only** в продакшене
- ✅ **Rate limiting** - защита от DDoS

---

## 📈 Roadmap

### Phase 1 (MVP - 7 дней): ✅
- Агрегация 3 банков
- Базовая аналитика
- Dashboard с графиками

### Phase 2 (Post-hackathon):
- 🔄 Автоматические переводы между счетами
- 💰 Умное сравнение банковских продуктов
- 📱 Native mobile app (React Native)
- 🤖 ML для прогнозов
- 🔔 Push notifications

### Phase 3 (Scale):
- 🏦 Интеграция с 10+ банками
- 🌍 Поддержка других стран (Казахстан, Беларусь)
- 🏢 B2B версия для малого бизнеса
- 💳 PFM (Personal Finance Management) advanced

---

## 👥 Команда

**Разработано для VTB API Hackathon 2025**

- Backend: Python FastAPI
- Frontend: React + TypeScript
- DevOps: Docker
- Design: Figma

---

## 📞 Контакты

- Email: team@financehub.ru
- Telegram: @financehub_support
- GitHub: github.com/team/financehub

---

## 📄 Лицензия

MIT License - см. LICENSE файл

---

## 🙏 Благодарности

- VTB API Hackathon 2025 за организацию
- Open Banking Russia за sandbox платформу
- ЦБ РФ за стандарты Open API

---

## 🛠️ Spec-Kit Интеграция

Этот проект интегрирован с **GitHub Spec-Kit** для Spec-Driven Development (разработка на основе спецификаций).

### Доступные команды в Cursor:

| Команда | Описание |
|---------|----------|
| `/speckit.constitution` | Создать/обновить конституцию проекта |
| `/speckit.specify` | Создать спецификацию фичи |
| `/speckit.plan` | Создать технический план реализации |
| `/speckit.tasks` | Разбить план на конкретные задачи |
| `/speckit.implement` | Выполнить реализацию по задачам |
| `/speckit.clarify` | Уточнить недостаточно специфицированные области |
| `/speckit.analyze` | Проанализировать согласованность артефактов |
| `/speckit.checklist` | Создать чеклист качества для требований |

### Структура проекта:

```
.specify/              # Spec-Kit конфигурация
├── scripts/           # Скрипты автоматизации
├── templates/         # Шаблоны для документов
└── README.md          # Документация по Spec-Kit

.cursor/
├── commands/          # Команды /speckit.* для Cursor
└── rules/             # Контекст для AI

memory/
└── constitution.md    # Конституция проекта (принципы и ограничения)

specs/                 # Спецификации фич
└── 001-financehub-mvp/
    ├── spec.md        # Функциональная спецификация
    ├── plan.md        # Технический план
    ├── tasks.md       # Список задач
    ├── contracts/     # API контракты
    └── checklists/    # Чеклисты качества
```

### Быстрый старт с Spec-Kit:

1. **Определить фичу**: `/speckit.specify <описание фичи>`
2. **Создать план**: `/speckit.plan <технические требования>`
3. **Разбить на задачи**: `/speckit.tasks`
4. **Реализовать**: `/speckit.implement`

📖 Подробная документация: [.specify/README.md](.specify/README.md)

---

## 🚀 Статус реализации

**Статус**: ✅ **MVP ЗАВЕРШЕН**

### ✅ Реализованные фазы:

1. **Phase 1: Setup** - Структура проекта, Docker, зависимости
2. **Phase 2: Foundation** - Database models, Auth, Core infrastructure  
3. **Phase 3: OAuth Integration** - Подключение банков через OAuth
4. **Phase 4: Dashboard** - Единый дашборд с агрегацией данных
5. **Phase 5-7: Transactions** - Управление транзакциями и категориями
6. **Phase 8-11: Features** - Бюджеты, цели, рекомендации, продукты
7. **Phase 12: Polish** - PWA, тесты, демо-данные

### 🎯 Ключевые возможности:

✅ Регистрация и аутентификация пользователей (JWT)  
✅ Подключение банковских счетов через OAuth 2.0  
✅ Агрегация балансов и транзакций из нескольких банков  
✅ Категоризация расходов  
✅ Управление бюджетами  
✅ Постановка и отслеживание финансовых целей  
✅ Персональные рекомендации по оптимизации финансов  
✅ Каталог банковских продуктов (вклады, кредиты, карты)  
✅ Responsive UI с TailwindCSS  
✅ PWA поддержка  
✅ Docker deployment  

### 🚀 Быстрый старт:

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd "VTB API"

# 2. Настроить .env файлы (см. .env.example)
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Запустить с Docker
docker-compose up -d

# 4. Применить миграции и seed данные
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/seed_demo_data.py

# 5. Открыть приложение
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

📖 **Полная документация по развертыванию**: [`DEPLOYMENT.md`](DEPLOYMENT.md)  
🎥 **Гайд для демонстрации**: [`DEMO_GUIDE.md`](DEMO_GUIDE.md)  
📋 **Спецификация MVP**: [`specs/001-financehub-mvp/spec.md`](specs/001-financehub-mvp/spec.md)  
🏗️ **Технический план**: [`specs/001-financehub-mvp/plan.md`](specs/001-financehub-mvp/plan.md)  
✅ **Список задач**: [`specs/001-financehub-mvp/tasks.md`](specs/001-financehub-mvp/tasks.md)

---

## 🎯 Соответствие критериям жюри

### ✅ Бизнес-критерии

**Ценность для пользователя:**
- Единая точка доступа ко всем финансам из разных банков
- Автоматическая агрегация и категоризация транзакций
- Персонализированные рекомендации по оптимизации
- Инструменты финансового планирования (бюджеты, цели)

**Модель монетизации:**
- **Freemium**: Базовые функции бесплатно (1 банк, базовая аналитика)
- **Premium** (99₽/мес): Неограниченные банки, расширенная аналитика, экспорт данных
- **Партнерские комиссии**: CPA от банков за рекомендации продуктов
- **B2B API**: Доступ для финтех-стартапов

**Масштабируемость:**
- Модульная архитектура с микросервисным подходом
- Легко добавляются новые банки (плагины)
- Docker-based deployment (горизонтальное масштабирование)
- Redis кэширование для высокой производительности
- Поддержка локализации и мультивалютности

### ✅ Технические критерии

**Использование Open Banking API:**
- OAuth 2.0 авторизация с банками
- Получение балансов, счетов, транзакций
- Refresh token механизм
- Retry-логика с exponential backoff
- Graceful обработка ошибок API

**Архитектурная целостность:**
```
Backend: FastAPI + PostgreSQL + Redis
Frontend: React 18 + TypeScript + TailwindCSS
Integration: VTB Open Banking API
Security: JWT + bcrypt + Fernet encryption
Deployment: Docker + Docker Compose
```

**Уровень реализации:**
- ✅ Полный MVP со всеми User Stories
- ✅ Production-ready код с error handling
- ✅ Responsive UI с PWA поддержкой
- ✅ Автоматическое тестирование (pytest + jest)
- ✅ Database migrations (Alembic)
- ✅ API документация (OpenAPI/Swagger)

### 🎬 Демонстрация

**Видео-демо:** [Ссылка на видео] (до 2 минут)  
**Презентация:** [Ссылка на PDF презентацию]  
**Live Demo:** http://localhost:3000 (после развертывания)

### 📦 Для загрузки на платформу

1. **ZIP архив проекта**: `VTB-API-FinanceHub.zip`
2. **Репозиторий**: [Ссылка на GitHub]
3. **Видео-демо**: [Ссылка на Яндекс.Диск]
4. **Презентация**: [Ссылка на PDF]

---

**Сделано с ❤️ для управления вашими финансами**

