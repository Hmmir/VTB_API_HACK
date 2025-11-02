# Tasks: FinanceHub MVP

**Feature**: Мультибанковское приложение для агрегации финансовых данных  
**Branch**: `001-financehub-mvp`  
**Input**: Design documents from `specs/001-financehub-mvp/`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3...)
- Exact file paths included in descriptions

## Path Conventions

- **Backend**: `backend/app/`
- **Frontend**: `frontend/src/`
- **Database**: `backend/alembic/versions/`
- **Tests**: `backend/tests/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure (backend/, frontend/, docker-compose.yml)
- [ ] T002 Initialize FastAPI backend with dependencies in backend/requirements.txt
- [ ] T003 [P] Initialize React + Vite frontend with dependencies in frontend/package.json
- [ ] T004 [P] Setup TailwindCSS configuration in frontend/tailwind.config.js
- [ ] T005 [P] Setup Docker Compose (PostgreSQL, Redis, backend, frontend) in docker-compose.yml
- [ ] T006 [P] Create .env.example files for backend and frontend
- [ ] T007 [P] Setup .gitignore for Python and Node.js projects
- [ ] T008 [P] Create README.md with setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Setup PostgreSQL database schema migrations with Alembic in backend/alembic/
- [ ] T010 [P] Create base SQLAlchemy models (Base, UUID, timestamps mixin) in backend/app/models/__init__.py
- [ ] T011 Create User model in backend/app/models/user.py
- [ ] T012 Create database.py (engine, SessionLocal) in backend/app/database.py
- [ ] T013 Setup JWT authentication utilities in backend/app/utils/security.py (hash_password, verify, create_jwt)
- [ ] T014 Setup encryption utilities in backend/app/utils/security.py (encrypt_token, decrypt_token with AES-256)
- [ ] T015 Create API dependencies (get_db, get_current_user) in backend/app/api/deps.py
- [ ] T016 Setup CORS middleware and exception handlers in backend/app/main.py
- [ ] T017 Create category seed data (Продукты, Транспорт, etc.) in backend/alembic/versions/002_seed_categories.py
- [ ] T018 [P] Setup Redux store and auth context in frontend/src/contexts/AuthContext.tsx
- [ ] T019 [P] Create Axios API client with JWT interceptors in frontend/src/services/api.ts
- [ ] T020 [P] Create reusable UI components (Button, Card, Input, Spinner) in frontend/src/components/common/
- [ ] T021 [P] Setup React Router with protected routes in frontend/src/App.tsx

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Подключение банковских счетов (Priority: P1) 🎯 MVP

**Goal**: Пользователь может подключить счета из разных банков через OAuth и увидеть их на дашборде

**Independent Test**: Подключить VBank через OAuth → увидеть балансы счетов на дашборде

### Implementation for User Story 1

**Backend - Models & Database**:

- [ ] T022 [P] [US1] Create BankConnection model in backend/app/models/bank_connection.py
- [ ] T023 [P] [US1] Create Account model in backend/app/models/account.py
- [ ] T024 [US1] Create migration for bank_connections and accounts tables in backend/alembic/versions/003_add_banks_accounts.py

**Backend - External API Clients**:

- [ ] T025 [P] [US1] Create base bank client abstract class in backend/app/integrations/base_bank_client.py
- [ ] T026 [P] [US1] Implement VBank API client in backend/app/integrations/vbank_client.py (OAuth, accounts, balances)
- [ ] T027 [P] [US1] Implement ABank API client in backend/app/integrations/abank_client.py (OAuth, accounts, balances)
- [ ] T028 [P] [US1] Implement SBank API client in backend/app/integrations/sbank_client.py (OAuth, accounts, balances)

**Backend - Services**:

- [ ] T029 [US1] Implement BankService in backend/app/services/bank_service.py (OAuth flow, token management)
- [ ] T030 [US1] Implement AggregationService in backend/app/services/aggregation_service.py (sync accounts from banks)

**Backend - API Endpoints**:

- [ ] T031 [US1] Implement POST /auth/register endpoint in backend/app/api/auth.py
- [ ] T032 [US1] Implement POST /auth/login endpoint in backend/app/api/auth.py (returns JWT)
- [ ] T033 [US1] Implement GET /banks endpoint in backend/app/api/banks.py (list available banks)
- [ ] T034 [US1] Implement POST /banks/connect endpoint in backend/app/api/banks.py (initiate OAuth)
- [ ] T035 [US1] Implement GET /banks/callback endpoint in backend/app/api/banks.py (OAuth callback handler)
- [ ] T036 [US1] Implement GET /accounts endpoint in backend/app/api/accounts.py (get aggregated accounts)

**Frontend - Auth Pages**:

- [ ] T037 [P] [US1] Create Register page in frontend/src/pages/Register.tsx
- [ ] T038 [P] [US1] Create Login page in frontend/src/pages/Login.tsx
- [ ] T039 [US1] Implement authentication service calls in frontend/src/services/auth.ts

**Frontend - Bank Connection**:

- [ ] T040 [P] [US1] Create BankConnectionModal component in frontend/src/components/banks/BankConnectionModal.tsx
- [ ] T041 [US1] Implement bank connection flow (OAuth redirect) in frontend/src/pages/Callback.tsx
- [ ] T042 [US1] Implement banks service calls in frontend/src/services/banks.ts

**Checkpoint**: User can register, login, connect banks via OAuth, and see connected banks

---

## Phase 4: User Story 2 - Просмотр агрегированной финансовой картины (Priority: P1) 🎯 MVP

**Goal**: Пользователь видит единый дашборд со всеми счетами, балансами и последними транзакциями

**Independent Test**: После подключения банков открыть дашборд → увидеть общий баланс и последние транзакции

### Implementation for User Story 2

**Backend - Services**:

- [ ] T043 [US2] Implement AnalyticsService.get_dashboard_summary() in backend/app/services/analytics_service.py (total balance, income, expenses)
- [ ] T044 [US2] Add get_recent_transactions() method to AggregationService in backend/app/services/aggregation_service.py

**Backend - API Endpoints**:

- [ ] T045 [US2] Implement GET /analytics/summary endpoint in backend/app/api/analytics.py (dashboard summary)
- [ ] T046 [US2] Add POST /accounts/sync endpoint in backend/app/api/accounts.py (manual sync trigger)

**Frontend - Dashboard Components**:

- [ ] T047 [P] [US2] Create BalanceWidget component in frontend/src/components/dashboard/BalanceWidget.tsx
- [ ] T048 [P] [US2] Create ExpensesWidget component in frontend/src/components/dashboard/ExpensesWidget.tsx
- [ ] T049 [P] [US2] Create IncomesWidget component in frontend/src/components/dashboard/IncomesWidget.tsx
- [ ] T050 [P] [US2] Create RecentTransactions component in frontend/src/components/dashboard/RecentTransactions.tsx
- [ ] T051 [US2] Create Dashboard page assembling all widgets in frontend/src/pages/Dashboard.tsx
- [ ] T052 [US2] Implement analytics service calls in frontend/src/services/analytics.ts

**Frontend - Accounts List**:

- [ ] T053 [P] [US2] Create AccountCard component in frontend/src/components/accounts/AccountCard.tsx
- [ ] T054 [P] [US2] Create BankLogo component in frontend/src/components/accounts/BankLogo.tsx
- [ ] T055 [US2] Create Accounts page in frontend/src/pages/Accounts.tsx
- [ ] T056 [US2] Implement accounts service calls in frontend/src/services/accounts.ts

**Checkpoint**: User sees unified dashboard with total balance, expenses, incomes, recent transactions

---

## Phase 5: User Story 3 - Просмотр и анализ транзакций (Priority: P2)

**Goal**: Пользователь видит все транзакции в одном списке с фильтрацией и поиском

**Independent Test**: Открыть страницу транзакций → применить фильтр по дате → увидеть отфильтрованный список

### Implementation for User Story 3

**Backend - Models & Database**:

- [ ] T057 [P] [US3] Create Transaction model in backend/app/models/transaction.py
- [ ] T058 [US3] Create migration for transactions table in backend/alembic/versions/004_add_transactions.py

**Backend - Services**:

- [ ] T059 [US3] Add sync_transactions() method to AggregationService in backend/app/services/aggregation_service.py
- [ ] T060 [US3] Implement TransactionService with filtering/search in backend/app/services/transaction_service.py

**Backend - API Endpoints**:

- [ ] T061 [US3] Implement GET /transactions endpoint with filters in backend/app/api/transactions.py (date_from, date_to, search, category_id)
- [ ] T062 [US3] Implement GET /transactions/{id} endpoint in backend/app/api/transactions.py

**Frontend - Transaction Components**:

- [ ] T063 [P] [US3] Create TransactionItem component in frontend/src/components/transactions/TransactionItem.tsx
- [ ] T064 [P] [US3] Create TransactionFilters component in frontend/src/components/transactions/TransactionFilters.tsx
- [ ] T065 [P] [US3] Create CategoryIcon component in frontend/src/components/transactions/CategoryIcon.tsx
- [ ] T066 [US3] Create TransactionList component in frontend/src/components/transactions/TransactionList.tsx
- [ ] T067 [US3] Create Transactions page in frontend/src/pages/Transactions.tsx
- [ ] T068 [US3] Implement transactions service calls in frontend/src/services/transactions.ts

**Checkpoint**: User can view, filter, and search all transactions from all banks

---

## Phase 6: User Story 4 - Автоматическая категоризация расходов (Priority: P2)

**Goal**: Система автоматически категоризирует транзакции

**Independent Test**: Загрузить транзакции → проверить что каждой присвоена категория

### Implementation for User Story 4

**Backend - Models & Database**:

- [ ] T069 [P] [US4] Create Category model in backend/app/models/category.py
- [ ] T070 [US4] Add category_id foreign key to Transaction model in backend/app/models/transaction.py

**Backend - Services**:

- [ ] T071 [US4] Implement CategorizationService.categorize_transaction() in backend/app/services/categorization_service.py (rule-based algorithm)
- [ ] T072 [US4] Create CATEGORY_KEYWORDS dictionary in backend/app/services/categorization_service.py
- [ ] T073 [US4] Integrate categorization into AggregationService.sync_transactions()

**Backend - API Endpoints**:

- [ ] T074 [US4] Implement GET /categories endpoint in backend/app/api/categories.py (list all categories)

**Frontend - Updates**:

- [ ] T075 [US4] Update TransactionItem component to display category icon and name
- [ ] T076 [US4] Implement categories service calls in frontend/src/services/categories.ts

**Checkpoint**: All transactions automatically categorized with visible icons

---

## Phase 7: User Story 5 - Аналитика расходов по категориям (Priority: P2)

**Goal**: Пользователь видит графики расходов по категориям

**Independent Test**: Открыть Analytics → увидеть круговую диаграмму расходов по категориям

### Implementation for User Story 5

**Backend - Services**:

- [ ] T077 [US5] Implement AnalyticsService.get_spending_by_category() in backend/app/services/analytics_service.py
- [ ] T078 [US5] Implement AnalyticsService.get_trends() in backend/app/services/analytics_service.py (line chart data)

**Backend - API Endpoints**:

- [ ] T079 [US5] Implement GET /analytics/spending endpoint in backend/app/api/analytics.py (pie chart data)
- [ ] T080 [US5] Implement GET /analytics/trends endpoint in backend/app/api/analytics.py (line chart data)

**Frontend - Analytics Components**:

- [ ] T081 [P] [US5] Create PieChart component (Recharts wrapper) in frontend/src/components/analytics/PieChart.tsx
- [ ] T082 [P] [US5] Create LineChart component (Recharts wrapper) in frontend/src/components/analytics/LineChart.tsx
- [ ] T083 [P] [US5] Create StatCard component in frontend/src/components/analytics/StatCard.tsx
- [ ] T084 [US5] Create Analytics page in frontend/src/pages/Analytics.tsx
- [ ] T085 [US5] Add period selector (current month, 3 months, 6 months) to Analytics page

**Checkpoint**: User sees visual analytics with pie charts and line graphs

---

## Phase 8: User Story 6 - Автоматическое создание бюджетов (Priority: P3)

**Goal**: Система автоматически создает бюджеты на основе истории трат

**Independent Test**: После накопления истории (3 мес.) система создает бюджеты → пользователь видит их с прогрессом

### Implementation for User Story 6

**Backend - Models & Database**:

- [ ] T086 [P] [US6] Create Budget model in backend/app/models/budget.py
- [ ] T087 [US6] Create migration for budgets table in backend/alembic/versions/005_add_budgets.py

**Backend - Services**:

- [ ] T088 [US6] Implement BudgetService.auto_create_budgets() in backend/app/services/budget_service.py (analyze last 3 months)
- [ ] T089 [US6] Implement BudgetService.update_budget_progress() in backend/app/services/budget_service.py (recalculate spent_amount)
- [ ] T090 [US6] Implement BudgetService.check_budget_alerts() in backend/app/services/budget_service.py (80%, 100% notifications)

**Backend - API Endpoints**:

- [ ] T091 [US6] Implement GET /budgets endpoint in backend/app/api/budgets.py (list all budgets)
- [ ] T092 [US6] Implement POST /budgets endpoint in backend/app/api/budgets.py (create budget, trigger auto-create)
- [ ] T093 [US6] Implement PUT /budgets/{id} endpoint in backend/app/api/budgets.py (update budget limit)
- [ ] T094 [US6] Implement DELETE /budgets/{id} endpoint in backend/app/api/budgets.py

**Frontend - Budget Components**:

- [ ] T095 [P] [US6] Create BudgetCard component in frontend/src/components/budgets/BudgetCard.tsx
- [ ] T096 [P] [US6] Create BudgetProgress component in frontend/src/components/budgets/BudgetProgress.tsx (progress bar)
- [ ] T097 [US6] Create Budgets page in frontend/src/pages/Budgets.tsx
- [ ] T098 [US6] Implement budgets service calls in frontend/src/services/budgets.ts

**Checkpoint**: System auto-creates budgets, shows progress, sends notifications

---

## Phase 9: User Story 7 - Постановка целей накоплений (Priority: P3)

**Goal**: Пользователь может ставить финансовые цели и отслеживать прогресс

**Independent Test**: Создать цель "Отпуск 100,000₽" → пополнить на 10,000₽ → увидеть 10% прогресс

### Implementation for User Story 7

**Backend - Models & Database**:

- [ ] T099 [P] [US7] Create Goal model in backend/app/models/goal.py
- [ ] T100 [US7] Create migration for goals table in backend/alembic/versions/006_add_goals.py

**Backend - Services**:

- [ ] T101 [US7] Implement GoalService CRUD methods in backend/app/services/goal_service.py
- [ ] T102 [US7] Implement GoalService.check_goal_achievement() in backend/app/services/goal_service.py

**Backend - API Endpoints**:

- [ ] T103 [US7] Implement GET /goals endpoint in backend/app/api/goals.py
- [ ] T104 [US7] Implement POST /goals endpoint in backend/app/api/goals.py
- [ ] T105 [US7] Implement PUT /goals/{id} endpoint in backend/app/api/goals.py (update current_amount)
- [ ] T106 [US7] Implement DELETE /goals/{id} endpoint in backend/app/api/goals.py

**Frontend - Goal Components**:

- [ ] T107 [P] [US7] Create GoalCard component in frontend/src/components/budgets/GoalCard.tsx
- [ ] T108 [P] [US7] Create GoalProgress component in frontend/src/components/budgets/GoalProgress.tsx
- [ ] T109 [US7] Add Goals section to Budgets page in frontend/src/pages/Budgets.tsx
- [ ] T110 [US7] Implement goals service calls in frontend/src/services/goals.ts

**Checkpoint**: User can create goals, update progress, see motivational messages

---

## Phase 10: User Story 8 - Персонализированные рекомендации (Priority: P3)

**Goal**: Пользователь получает рекомендации по оптимизации финансов

**Independent Test**: После накопления истории → увидеть инсайты и product recommendations

### Implementation for User Story 8

**Backend - Models & Database**:

- [ ] T111 [P] [US8] Create BankProduct model in backend/app/models/bank_product.py
- [ ] T112 [P] [US8] Create Recommendation model in backend/app/models/recommendation.py
- [ ] T113 [US8] Create migration for bank_products and recommendations tables in backend/alembic/versions/007_add_recommendations.py

**Backend - Services**:

- [ ] T114 [US8] Implement ProductService.sync_bank_products() in backend/app/services/product_service.py (fetch from Products API)
- [ ] T115 [US8] Implement RecommendationService.generate_insights() in backend/app/services/recommendation_service.py (spending trends)
- [ ] T116 [US8] Implement RecommendationService.compare_products() in backend/app/services/recommendation_service.py

**Backend - API Endpoints**:

- [ ] T117 [US8] Implement GET /recommendations endpoint in backend/app/api/recommendations.py
- [ ] T118 [US8] Implement PUT /recommendations/{id}/view endpoint in backend/app/api/recommendations.py
- [ ] T119 [US8] Implement PUT /recommendations/{id}/dismiss endpoint in backend/app/api/recommendations.py

**Frontend - Recommendation Components**:

- [ ] T120 [P] [US8] Create InsightCard component in frontend/src/components/recommendations/InsightCard.tsx
- [ ] T121 [US8] Add Recommendations section to Dashboard in frontend/src/pages/Dashboard.tsx
- [ ] T122 [US8] Implement recommendations service calls in frontend/src/services/recommendations.ts

**Checkpoint**: User sees personalized insights and product recommendations

---

## Phase 11: User Story 9 - Сравнение банковских продуктов (Priority: P3)

**Goal**: Пользователь может сравнивать банковские продукты (вклады, кредиты, карты)

**Independent Test**: Открыть Products → выбрать "Вклады" → увидеть таблицу с сортировкой по ставке

### Implementation for User Story 9

**Backend - API Endpoints**:

- [ ] T123 [US9] Implement GET /products endpoint in backend/app/api/products.py (list products with filters)
- [ ] T124 [US9] Implement GET /products/{id} endpoint in backend/app/api/products.py (product details)

**Frontend - Product Components**:

- [ ] T125 [P] [US9] Create ProductCard component in frontend/src/components/recommendations/ProductCard.tsx
- [ ] T126 [P] [US9] Create ProductTable component in frontend/src/components/products/ProductTable.tsx
- [ ] T127 [US9] Create Products page in frontend/src/pages/Products.tsx
- [ ] T128 [US9] Implement products service calls in frontend/src/services/products.ts

**Checkpoint**: User can browse, filter, and compare bank products

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Finishing touches, error handling, performance optimization

- [ ] T129 [P] Implement retry logic with exponential backoff in backend/app/utils/retry.py
- [ ] T130 [P] Setup Redis caching for bank API responses in backend/app/utils/cache.py
- [ ] T131 [P] Add comprehensive error handling middleware in backend/app/main.py
- [ ] T132 [P] Implement rate limiting (100 req/min per user) in backend/app/main.py
- [ ] T133 [P] Setup structured logging with correlation IDs in backend/app/utils/logging.py
- [ ] T134 [P] Add loading states and error messages to all frontend pages
- [ ] T135 [P] Implement toast notifications in frontend/src/components/common/Toast.tsx
- [ ] T136 [P] Setup PWA manifest and service worker in frontend/public/manifest.json
- [ ] T137 [P] Add responsive design breakpoints for mobile in frontend/src/index.css
- [ ] T138 [P] Optimize bundle size (code splitting, lazy loading) in frontend/vite.config.ts
- [ ] T139 [P] Add pagination to transactions list (50 per page)
- [ ] T140 [P] Write backend unit tests for services in backend/tests/
- [ ] T141 [P] Write frontend component tests in frontend/tests/
- [ ] T142 Create comprehensive README with setup instructions
- [ ] T143 Record 2-minute video demo
- [ ] T144 Create presentation slides (PDF)

**Checkpoint**: All polish tasks complete, app ready for demo

---

## Task Summary

**Total Tasks**: 144

### By Phase:
- Phase 1 (Setup): 8 tasks
- Phase 2 (Foundation): 13 tasks
- Phase 3 (US1 - P1): 21 tasks
- Phase 4 (US2 - P1): 14 tasks
- Phase 5 (US3 - P2): 12 tasks
- Phase 6 (US4 - P2): 8 tasks
- Phase 7 (US5 - P2): 9 tasks
- Phase 8 (US6 - P3): 13 tasks
- Phase 9 (US7 - P3): 12 tasks
- Phase 10 (US8 - P3): 12 tasks
- Phase 11 (US9 - P3): 6 tasks
- Phase 12 (Polish): 16 tasks

### By Priority:
- P1 tasks (US1, US2): 35 tasks - **MVP Critical**
- P2 tasks (US3, US4, US5): 29 tasks
- P3 tasks (US6, US7, US8, US9): 43 tasks
- Foundation + Polish: 37 tasks

### Parallel Opportunities:
- Phase 1: 6 parallel tasks
- Phase 2: 6 parallel tasks
- User Stories: 40+ parallel tasks (models, components)
- Phase 12: 14 parallel tasks

**Total Parallelizable**: ~66 tasks (45%)

---

## Dependencies & Execution Order

### Critical Path (Must be sequential):
1. Phase 1 (Setup) → Phase 2 (Foundation)
2. Foundation MUST complete before any User Story
3. US1 (P1) SHOULD complete before US2-US9 (provides bank connections)
4. US4 (Categorization) SHOULD complete before US5 (Analytics by category)
5. US6 (Budgets) requires US4 (Categories)

### Independent User Stories (Can be parallel after Foundation):
- US3 (Transactions) - independent after Foundation
- US7 (Goals) - fully independent
- US9 (Products) - fully independent

### Suggested Implementation Order:
1. **Week 1 (Days 1-2)**: Phase 1 + Phase 2 + US1 (Auth + Banks + OAuth) → MVP Checkpoint 1
2. **Week 1 (Days 3-4)**: US2 (Dashboard) + US3 (Transactions) → MVP Checkpoint 2
3. **Week 1 (Days 5-6)**: US4 (Categorization) + US5 (Analytics) → Feature Complete
4. **Week 1 (Day 7)**: US6 (Budgets) + Phase 12 (Polish) → Demo Ready
5. **Post-MVP (if time)**: US7, US8, US9 (Goals, Recommendations, Products)

---

## MVP Definition (Minimal Viable Product)

**MVP Scope**: US1 + US2 (P1 only) + Foundation + Basic Polish

**MVP Tasks**: T001-T056 + T129-T132 + T142-T144 = **~70 tasks**

**MVP delivers**:
- ✅ User authentication
- ✅ Connect 3 banks via OAuth
- ✅ Aggregated dashboard (balance, expenses, incomes)
- ✅ View transactions from all banks
- ✅ Error handling and caching
- ✅ Documentation and demo

**Timeline**: 3-4 days for experienced developer

---

## Next Steps

1. ✅ Tasks defined and organized by user story
2. ⏭️ Run `/speckit.implement` to execute implementation
3. ⏭️ Follow task order (Setup → Foundation → US1 → US2 → ...)
4. ⏭️ Mark tasks as complete: `- [X]` in this file
5. ⏭️ Validate each checkpoint before proceeding
6. ⏭️ Test MVP after US1+US2 complete
7. ⏭️ Continue with P2 and P3 features
8. ⏭️ Record demo and create presentation

---

**Ready for Implementation**: Yes ✅  
**Estimated Completion Time**: 7 days (with polish)  
**MVP Delivery**: 3-4 days (US1+US2 only)

