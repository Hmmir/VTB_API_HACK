# Implementation Plan: FinanceHub MVP

**Branch**: `001-financehub-mvp` | **Date**: 2025-10-28 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-financehub-mvp/spec.md`

## Summary

FinanceHub MVP — мультибанковское приложение для агрегации финансовых данных из нескольких банков через Open Banking API с единым дашбордом, умной аналитикой расходов, автоматическим управлением бюджетом и персонализированными рекомендациями.

**Техническая стратегия**: Full-stack web application с Python FastAPI backend, PostgreSQL database, Redis caching layer, React + TypeScript frontend, интеграция с VTB Open Banking API через OAuth 2.0.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5+ (frontend)  
**Primary Dependencies**:
- **Backend**: FastAPI 0.104+, SQLAlchemy 2.0+, Pydantic 2.0+, httpx (async HTTP), python-jose (JWT), passlib (password hashing), alembic (migrations)
- **Frontend**: React 18+, Vite 5+, TailwindCSS 3+, Recharts 2+ (charts), React Router 6+, Axios (HTTP client), date-fns (date utils)
- **Infrastructure**: PostgreSQL 15+, Redis 7+, Docker, Docker Compose

**Storage**: PostgreSQL 15 (relational data: users, accounts, transactions, budgets), Redis 7 (caching, session storage)  
**Testing**: pytest (backend unit/integration), Jest + React Testing Library (frontend)  
**Target Platform**: Web (desktop + mobile PWA), deployed as Docker containers  
**Project Type**: Web application (separate backend + frontend)  
**Performance Goals**:
- API response time: < 200ms (p95)
- Dashboard load time: < 2s with cached data
- Support 100 concurrent users without degradation
- Bank API sync: < 5s for 1000 transactions per user

**Constraints**:
- OAuth 2.0 flow must complete in < 60s
- Token storage must be encrypted (AES-256)
- Must handle bank API failures gracefully (retry logic, fallback to cache)
- Must respect bank API rate limits (implement throttling)
- Sandbox environment: VTB Open Banking API at https://ift.rtuitlab.dev/

**Scale/Scope**:
- MVP target: 10,000 users
- Expected data volume: ~100K transactions per day
- 3 banks initially (VBank, ABank, SBank)
- 9 user stories (P1: 2, P2: 3, P3: 4)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Принципы из Constitution

✅ **Simplicity First**: Используем proven стек (FastAPI + React), избегаем overengineering  
✅ **User Value**: Каждая фича решает реальную проблему (фрагментация данных)  
✅ **Scalability**: Plugin architecture для банков, легко добавлять новые  
✅ **Security**: OAuth 2.0, encrypted tokens, JWT, HTTPS only  
✅ **Performance**: Redis caching, async I/O, lazy loading

### Technical Constraints

✅ **Backend**: Python 3.11+ с FastAPI ✓  
✅ **Database**: PostgreSQL 15 ✓  
✅ **Cache**: Redis 7 ✓  
✅ **Frontend**: React 18 + TypeScript ✓  
✅ **API Standard**: Open Banking Russia v2.1 ✓  
✅ **Authentication**: OAuth 2.0 + JWT ✓  
✅ **Deployment**: Docker + Docker Compose ✓

### Must-Have Features (MVP)

✅ **FR-001 to FR-007**: User authentication (JWT) → Phase 2  
✅ **FR-008 to FR-015**: Multi-bank OAuth integration → Phase 2  
✅ **FR-016 to FR-020**: Account aggregation → Phase 2  
✅ **FR-021 to FR-026**: Transaction list → Phase 3  
✅ **FR-027 to FR-031**: Automatic categorization → Phase 3  
✅ **FR-038 to FR-043**: Budget management system → Phase 4  
✅ **FR-032 to FR-037**: Analytics dashboard with charts → Phase 3  
✅ **FR-016 to FR-020**: Responsive PWA design → Phase 5

**VERDICT**: ✅ All constitution checks pass. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```
specs/001-financehub-mvp/
├── spec.md              # Feature specification (already created)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (technology decisions)
├── data-model.md        # Phase 1 output (database schema, entities)
├── quickstart.md        # Phase 1 output (setup instructions)
├── contracts/           # Phase 1 output (API specifications)
│   ├── api-spec.yaml    # OpenAPI 3.0 specification
│   └── bank-api-examples.md  # Example requests/responses from banks
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```
financehub/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration (env vars, settings)
│   │   ├── database.py          # SQLAlchemy engine, session
│   │   │
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User model
│   │   │   ├── bank_connection.py  # BankConnection model
│   │   │   ├── account.py       # Account model
│   │   │   ├── transaction.py   # Transaction model
│   │   │   ├── category.py      # Category model
│   │   │   ├── budget.py        # Budget model
│   │   │   ├── goal.py          # Goal model
│   │   │   ├── bank_product.py  # BankProduct model
│   │   │   └── recommendation.py # Recommendation model
│   │   │
│   │   ├── schemas/             # Pydantic schemas (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User DTOs
│   │   │   ├── bank.py          # Bank DTOs
│   │   │   ├── account.py       # Account DTOs
│   │   │   ├── transaction.py   # Transaction DTOs
│   │   │   ├── analytics.py     # Analytics DTOs
│   │   │   ├── budget.py        # Budget DTOs
│   │   │   └── recommendation.py # Recommendation DTOs
│   │   │
│   │   ├── api/                 # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── deps.py          # Dependencies (get_db, get_current_user)
│   │   │   ├── auth.py          # POST /auth/register, /auth/login
│   │   │   ├── banks.py         # POST /banks/connect, GET /banks
│   │   │   ├── accounts.py      # GET /accounts, GET /accounts/{id}
│   │   │   ├── transactions.py  # GET /transactions (with filters)
│   │   │   ├── analytics.py     # GET /analytics/spending, /analytics/trends
│   │   │   ├── budgets.py       # GET /budgets, POST /budgets, PUT /budgets/{id}
│   │   │   ├── goals.py         # CRUD for goals
│   │   │   ├── products.py      # GET /products (bank products catalog)
│   │   │   └── recommendations.py # GET /recommendations
│   │   │
│   │   ├── services/            # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py  # User registration, login, JWT
│   │   │   ├── bank_service.py  # OAuth flow, token management
│   │   │   ├── aggregation_service.py  # Sync data from banks
│   │   │   ├── categorization_service.py  # Auto-categorize transactions
│   │   │   ├── analytics_service.py  # Calculate stats, trends
│   │   │   ├── budget_service.py  # Auto-create budgets, track progress
│   │   │   ├── recommendation_service.py  # Generate insights
│   │   │   └── product_service.py  # Compare bank products
│   │   │
│   │   ├── integrations/        # External API clients
│   │   │   ├── __init__.py
│   │   │   ├── base_bank_client.py  # Abstract base class
│   │   │   ├── vbank_client.py  # VBank API client
│   │   │   ├── abank_client.py  # ABank API client
│   │   │   └── sbank_client.py  # SBank API client
│   │   │
│   │   └── utils/               # Helper utilities
│   │       ├── __init__.py
│   │       ├── security.py      # Password hashing, JWT, encryption
│   │       ├── cache.py         # Redis cache wrapper
│   │       └── retry.py         # Exponential backoff retry logic
│   │
│   ├── alembic/                 # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── tests/                   # Backend tests
│   │   ├── conftest.py          # Pytest fixtures
│   │   ├── test_auth.py
│   │   ├── test_banks.py
│   │   ├── test_aggregation.py
│   │   └── test_categorization.py
│   │
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Example environment variables
│   ├── Dockerfile               # Backend container
│   └── README.md                # Backend setup instructions
│
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   ├── manifest.json        # PWA manifest
│   │   └── icons/               # PWA icons
│   │
│   ├── src/
│   │   ├── main.tsx             # React entry point
│   │   ├── App.tsx              # Root component
│   │   ├── index.css            # Global styles (TailwindCSS)
│   │   │
│   │   ├── components/          # Reusable UI components
│   │   │   ├── common/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   └── Spinner.tsx
│   │   │   │
│   │   │   ├── dashboard/
│   │   │   │   ├── BalanceWidget.tsx
│   │   │   │   ├── ExpensesWidget.tsx
│   │   │   │   ├── IncomesWidget.tsx
│   │   │   │   └── RecentTransactions.tsx
│   │   │   │
│   │   │   ├── accounts/
│   │   │   │   ├── AccountCard.tsx
│   │   │   │   └── BankLogo.tsx
│   │   │   │
│   │   │   ├── transactions/
│   │   │   │   ├── TransactionList.tsx
│   │   │   │   ├── TransactionItem.tsx
│   │   │   │   ├── TransactionFilters.tsx
│   │   │   │   └── CategoryIcon.tsx
│   │   │   │
│   │   │   ├── analytics/
│   │   │   │   ├── PieChart.tsx        # Recharts wrapper
│   │   │   │   ├── LineChart.tsx       # Recharts wrapper
│   │   │   │   └── StatCard.tsx
│   │   │   │
│   │   │   ├── budgets/
│   │   │   │   ├── BudgetCard.tsx
│   │   │   │   ├── BudgetProgress.tsx
│   │   │   │   ├── GoalCard.tsx
│   │   │   │   └── GoalProgress.tsx
│   │   │   │
│   │   │   └── recommendations/
│   │   │       ├── InsightCard.tsx
│   │   │       └── ProductCard.tsx
│   │   │
│   │   ├── pages/               # Page-level components
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Accounts.tsx
│   │   │   ├── Transactions.tsx
│   │   │   ├── Analytics.tsx
│   │   │   ├── Budgets.tsx
│   │   │   ├── Products.tsx
│   │   │   └── Settings.tsx
│   │   │
│   │   ├── services/            # API client layer
│   │   │   ├── api.ts           # Axios instance with interceptors
│   │   │   ├── auth.ts          # Auth API calls
│   │   │   ├── banks.ts         # Banks API calls
│   │   │   ├── accounts.ts      # Accounts API calls
│   │   │   ├── transactions.ts  # Transactions API calls
│   │   │   ├── analytics.ts     # Analytics API calls
│   │   │   └── budgets.ts       # Budgets API calls
│   │   │
│   │   ├── contexts/            # React Context providers
│   │   │   ├── AuthContext.tsx  # User auth state
│   │   │   └── ThemeContext.tsx # Theme (light/dark)
│   │   │
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useAuth.ts       # Auth hook
│   │   │   ├── useAccounts.ts   # Accounts data hook
│   │   │   └── useTransactions.ts # Transactions data hook
│   │   │
│   │   ├── types/               # TypeScript type definitions
│   │   │   ├── user.ts
│   │   │   ├── bank.ts
│   │   │   ├── account.ts
│   │   │   ├── transaction.ts
│   │   │   └── budget.ts
│   │   │
│   │   └── utils/               # Helper functions
│   │       ├── format.ts        # Date, currency formatting
│   │       └── validation.ts    # Form validation
│   │
│   ├── tests/                   # Frontend tests
│   │   └── components/
│   │       └── Dashboard.test.tsx
│   │
│   ├── package.json             # Node dependencies
│   ├── tsconfig.json            # TypeScript config
│   ├── vite.config.ts           # Vite config
│   ├── tailwind.config.js       # TailwindCSS config
│   ├── Dockerfile               # Frontend container
│   └── README.md                # Frontend setup instructions
│
├── docker-compose.yml           # Orchestrate all services
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore patterns
└── README.md                    # Project README

```

**Structure Decision**: Выбрана структура Web application (Option 2) с разделением backend и frontend, так как:
1. Spec явно указывает на web-приложение с API и UI
2. Backend и frontend имеют разные tech stacks (Python vs TypeScript)
3. Возможность независимого масштабирования и деплоя
4. Соответствует best practices для modern full-stack apps

## Phase 0: Research & Technology Decisions

### Research Tasks

1. **Open Banking API Integration**
   - Изучить документацию VTB Open Banking API (sandbox)
   - Протестировать OAuth 2.0 flow с VBank, ABank, SBank
   - Изучить формат responses (accounts, transactions, products)
   - Определить rate limits и best practices

2. **FastAPI Best Practices**
   - Архитектура для async/await patterns
   - Dependency injection для database sessions
   - Background tasks для синхронизации данных
   - Error handling middleware

3. **React + TypeScript + Vite**
   - Project setup с Vite (быстрее CRA)
   - TailwindCSS integration
   - Recharts для визуализации
   - PWA configuration (manifest, service worker)

4. **Security & Encryption**
   - JWT token best practices (короткий access, долгий refresh)
   - AES-256 encryption для хранения bank tokens
   - CORS configuration для production
   - Rate limiting strategy

5. **Caching Strategy**
   - Redis для session storage
   - Cache bank API responses (TTL: 1 hour)
   - Cache invalidation strategy
   - Optimistic updates в UI

### Output: research.md

Файл `research.md` будет содержать:
- Выбор библиотек с обоснованием
- Примеры интеграции с VTB API
- Архитектурные паттерны
- Performance optimization strategies

## Phase 1: Design & Contracts

### Data Model (data-model.md)

**Entities**:

1. **User** (users table)
   - id: UUID (PK)
   - email: VARCHAR(255) UNIQUE
   - hashed_password: VARCHAR(255)
   - created_at: TIMESTAMP
   - status: ENUM('active', 'blocked')

2. **BankConnection** (bank_connections table)
   - id: UUID (PK)
   - user_id: UUID (FK -> users.id)
   - bank_id: VARCHAR(50) ('vbank', 'abank', 'sbank')
   - encrypted_access_token: TEXT
   - refresh_token: TEXT
   - consent_id: VARCHAR(255)
   - status: ENUM('active', 'expired', 'revoked')
   - last_sync_at: TIMESTAMP
   - created_at: TIMESTAMP

3. **Account** (accounts table)
   - id: UUID (PK)
   - bank_connection_id: UUID (FK -> bank_connections.id)
   - account_id_from_bank: VARCHAR(255)
   - account_type: VARCHAR(50) ('current', 'savings', 'card')
   - currency: VARCHAR(3) (default 'RUB')
   - balance: DECIMAL(15, 2)
   - bank_name: VARCHAR(100)
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

4. **Transaction** (transactions table)
   - id: UUID (PK)
   - account_id: UUID (FK -> accounts.id)
   - transaction_id_from_bank: VARCHAR(255) UNIQUE
   - date: DATE
   - amount: DECIMAL(15, 2)
   - description: TEXT
   - category_id: UUID (FK -> categories.id)
   - transaction_type: ENUM('income', 'expense')
   - raw_data: JSONB (original response from bank)
   - created_at: TIMESTAMP

5. **Category** (categories table)
   - id: UUID (PK)
   - name: VARCHAR(100) ('Продукты', 'Транспорт', etc.)
   - icon: VARCHAR(50)
   - keywords: TEXT[] (array of keywords)
   - created_at: TIMESTAMP

6. **Budget** (budgets table)
   - id: UUID (PK)
   - user_id: UUID (FK -> users.id)
   - category_id: UUID (FK -> categories.id)
   - limit_amount: DECIMAL(15, 2)
   - spent_amount: DECIMAL(15, 2)
   - period: VARCHAR(20) ('monthly')
   - period_start: DATE
   - period_end: DATE
   - status: ENUM('on_track', 'warning', 'exceeded')
   - auto_created: BOOLEAN
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

7. **Goal** (goals table)
   - id: UUID (PK)
   - user_id: UUID (FK -> users.id)
   - name: VARCHAR(255)
   - target_amount: DECIMAL(15, 2)
   - current_amount: DECIMAL(15, 2)
   - status: ENUM('active', 'achieved', 'archived')
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

8. **BankProduct** (bank_products table)
   - id: UUID (PK)
   - bank_name: VARCHAR(100)
   - product_type: VARCHAR(50) ('deposit', 'credit', 'card')
   - name: VARCHAR(255)
   - interest_rate: DECIMAL(5, 2)
   - term_months: INTEGER
   - min_amount: DECIMAL(15, 2)
   - description: TEXT
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

9. **Recommendation** (recommendations table)
   - id: UUID (PK)
   - user_id: UUID (FK -> users.id)
   - type: VARCHAR(50) ('insight', 'product', 'saving_tip')
   - title: VARCHAR(255)
   - description: TEXT
   - priority: INTEGER
   - status: ENUM('new', 'viewed', 'dismissed')
   - bank_product_id: UUID (FK -> bank_products.id, nullable)
   - created_at: TIMESTAMP

**Indexes**:
- users.email (UNIQUE)
- transactions.account_id + date (для быстрых запросов по периоду)
- transactions.category_id (для аналитики)
- budgets.user_id + period_start (для быстрого поиска текущих бюджетов)

### API Contracts (contracts/api-spec.yaml)

**OpenAPI 3.0 specification** с endpoints:

**Authentication**:
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login (returns JWT)
- `POST /api/v1/auth/refresh` - Refresh JWT token

**Banks**:
- `GET /api/v1/banks` - List available banks
- `POST /api/v1/banks/connect` - Initiate OAuth flow
- `GET /api/v1/banks/callback` - OAuth callback handler
- `DELETE /api/v1/banks/{bank_id}` - Disconnect bank

**Accounts**:
- `GET /api/v1/accounts` - List all user accounts (aggregated)
- `GET /api/v1/accounts/{id}` - Get account details
- `POST /api/v1/accounts/sync` - Manually trigger sync

**Transactions**:
- `GET /api/v1/transactions` - List transactions (with filters: date_from, date_to, category_id, search)
- `GET /api/v1/transactions/{id}` - Get transaction details

**Analytics**:
- `GET /api/v1/analytics/spending` - Spending by categories (pie chart data)
- `GET /api/v1/analytics/trends` - Trends over time (line chart data)
- `GET /api/v1/analytics/summary` - Dashboard summary (total balance, income, expenses)

**Budgets**:
- `GET /api/v1/budgets` - List all budgets
- `POST /api/v1/budgets` - Create budget (manual or auto)
- `PUT /api/v1/budgets/{id}` - Update budget
- `DELETE /api/v1/budgets/{id}` - Delete budget

**Goals**:
- `GET /api/v1/goals` - List all goals
- `POST /api/v1/goals` - Create goal
- `PUT /api/v1/goals/{id}` - Update goal progress
- `DELETE /api/v1/goals/{id}` - Delete goal

**Products**:
- `GET /api/v1/products` - List bank products (with filters: type, bank)
- `GET /api/v1/products/{id}` - Get product details

**Recommendations**:
- `GET /api/v1/recommendations` - List personalized recommendations
- `PUT /api/v1/recommendations/{id}/view` - Mark as viewed
- `PUT /api/v1/recommendations/{id}/dismiss` - Dismiss recommendation

### Quickstart (quickstart.md)

**Setup instructions**:

1. Clone repository
2. Setup backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with VTB API credentials
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

3. Setup frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. Docker (production):
   ```bash
   docker-compose up -d
   ```

## Implementation Phases

### Phase 2: Core Backend (Days 1-2)

**Goal**: Implement authentication, database models, bank OAuth integration.

**Tasks**:
1. Setup FastAPI project with SQLAlchemy
2. Implement User model + authentication (JWT)
3. Create database migrations (Alembic)
4. Implement BankConnection model + OAuth flow
5. Create bank API clients (VBank, ABank, SBank)
6. Implement aggregation service (sync accounts + transactions)

**Deliverables**:
- Working REST API for auth + bank connection
- Database with migrations
- OAuth flow working with 3 banks

### Phase 3: Transactions & Analytics (Day 3)

**Goal**: Implement transaction listing, categorization, analytics endpoints.

**Tasks**:
1. Implement Transaction model
2. Create categorization service (rule-based)
3. Implement analytics service (spending by category, trends)
4. Create API endpoints for transactions + analytics

**Deliverables**:
- Transactions API with filters
- Auto-categorization working
- Analytics endpoints returning chart data

### Phase 4: Budgeting & Goals (Day 4)

**Goal**: Implement automatic budget creation, goals, notifications.

**Tasks**:
1. Implement Budget model
2. Create budget service (auto-create based on history)
3. Implement Goal model
4. Create recommendation service (generate insights)
5. Implement notification logic (80%, exceeded)

**Deliverables**:
- Budgets API working
- Goals API working
- Recommendations generated

### Phase 5: Frontend UI (Days 5-6)

**Goal**: Build React frontend with all pages and components.

**Tasks**:
1. Setup React + Vite + TailwindCSS
2. Implement authentication pages (Login, Register)
3. Create Dashboard page with widgets
4. Create Transactions page with filters
5. Create Analytics page with charts (Recharts)
6. Create Budgets page with progress bars
7. Create Products comparison page
8. Implement responsive design (mobile-first)
9. Setup PWA (manifest, icons, service worker)

**Deliverables**:
- Fully functional UI
- All pages implemented
- PWA working

### Phase 6: Polish & Testing (Day 7)

**Goal**: Testing, documentation, deployment, video demo.

**Tasks**:
1. Write backend tests (pytest)
2. Write frontend tests (Jest)
3. Setup Docker Compose
4. Create deployment documentation
5. Test full user flows
6. Record video demo (2 min)
7. Create presentation slides (PDF)

**Deliverables**:
- Tests passing
- Docker setup working
- Documentation complete
- Video demo ready
- Presentation ready

## Testing Strategy

**Backend Tests**:
- Unit tests для services (categorization, analytics, budget creation)
- Integration tests для API endpoints
- Mocking bank API responses

**Frontend Tests**:
- Component tests для ключевых компонентов (Dashboard, Charts)
- E2E tests для критичных flows (login → connect bank → view transactions)

**Manual Testing**:
- OAuth flow с реальными банками (sandbox)
- Error handling (bank API failures)
- Performance (load time, API response time)

## Deployment

**Development**:
- Backend: `uvicorn app.main:app --reload`
- Frontend: `npm run dev`

**Production**:
- Docker Compose с 4 контейнерами:
  1. PostgreSQL
  2. Redis
  3. Backend (FastAPI)
  4. Frontend (Nginx serving static build)

**Environment Variables** (`.env`):
```
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/financehub
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=<random-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# VTB API
VTB_TEAM_ID=team010-1
VTB_TEAM_SECRET=<your-secret>
VTB_API_BASE_URL=https://ift.rtuitlab.dev
VTB_OAUTH_CALLBACK=http://localhost:3000/callback

# Banks
VBANK_CLIENT_ID=<client-id>
ABANK_CLIENT_ID=<client-id>
SBANK_CLIENT_ID=<client-id>
```

## Risk Management

**Technical Risks**:
1. **Bank API unavailability**: Mitigation: caching, retry logic, fallback to stale data
2. **OAuth flow complexity**: Mitigation: early testing, detailed documentation
3. **Performance with large datasets**: Mitigation: pagination, indexes, caching
4. **Category accuracy**: Mitigation: iterative improvement of keywords dictionary

**Timeline Risks**:
1. **7-day constraint**: Mitigation: strict MVP scope, prioritize P1 features
2. **Integration delays**: Mitigation: mock bank responses early, parallel development

## Monitoring & Observability

**Logging**:
- Structured logging (JSON format)
- Log levels: DEBUG (dev), INFO (prod)
- Log all bank API requests/responses
- Log all authentication attempts

**Metrics**:
- API response times (p50, p95, p99)
- Bank API success rate
- User registration/login rate
- Feature usage (transactions viewed, budgets created)

**Alerts**:
- Bank API failure rate > 10%
- API response time > 1s
- Database connection errors

## Next Steps

1. ✅ Review constitution check (PASSED)
2. ⏭️ Run `/speckit.tasks` to generate task breakdown
3. ⏭️ Run `/speckit.implement` to execute implementation

---

**Ready for Task Generation**: Yes ✅  
**Ready for Implementation**: After `/speckit.tasks` completes
