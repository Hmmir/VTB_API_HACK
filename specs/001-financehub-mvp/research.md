# Technology Research: FinanceHub MVP

**Date**: 2025-10-28  
**Purpose**: Document technology choices, alternatives considered, and implementation decisions

## 1. Open Banking API Integration

### Decision: VTB Open Banking API (Sandbox)

**Chosen**: VTB Open Banking API через https://ift.rtuitlab.dev/

**Rationale**:
- Официальный sandbox для хакатона
- Поддерживает стандарт Open Banking Russia v2.1
- Доступны 3 виртуальных банка (VBank, ABank, SBank)
- Полная документация и примеры

**Implementation Details**:
```python
# Base URL
BASE_URL = "https://ift.rtuitlab.dev"

# Authentication
# POST /auth/bank-token
# Body: {"teamId": "team010-1", "teamSecret": "<secret>"}
# Response: {"access_token": "...", "expires_in": 3600}

# Consent Request
# POST /account-consents/request
# Headers: {"Authorization": "Bearer <bank_token>"}
# Body: {
#   "userClientId": "user-123",
#   "permissions": ["ReadAccountsBasic", "ReadBalances", "ReadTransactions"]
# }

# Accounts
# GET /accounts
# Headers: {"Authorization": "Bearer <bank_token>", "x-fapi-customer-consent-id": "<consent_id>"}

# Transactions
# GET /accounts/{accountId}/transactions
# Query params: ?fromDate=2024-01-01&toDate=2024-12-31
```

**Rate Limits**:
- 100 requests per minute per team
- 1000 requests per day per team
- Mitigation: Redis caching с TTL 1 hour

**Error Handling**:
- 401 Unauthorized → refresh token
- 403 Forbidden → consent revoked, prompt user to reconnect
- 429 Too Many Requests → exponential backoff
- 500/503 Server Error → retry 3 times, then fallback to cache

### Alternatives Considered:

❌ **Real bank APIs**: Нет доступа без лицензии ЦБ  
❌ **Mock APIs**: Не демонстрирует реальную интеграцию

---

## 2. Backend Framework

### Decision: FastAPI 0.104+

**Chosen**: FastAPI with Python 3.11+

**Rationale**:
- **High Performance**: Async/await support, comparable to Node.js/Go
- **Type Safety**: Pydantic validation, автоматическая документация
- **Developer Experience**: Auto-generated OpenAPI/Swagger docs
- **Modern**: Активная community, регулярные updates

**Key Features Used**:
- Dependency Injection для database sessions
- Background tasks для sync operations
- Middleware для CORS, authentication
- Pydantic models для request/response validation

**Example**:
```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

app = FastAPI(title="FinanceHub API", version="1.0.0")

@app.get("/accounts", response_model=List[AccountSchema])
async def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await account_service.get_user_accounts(db, current_user.id)
```

### Alternatives Considered:

❌ **Django**: Слишком тяжеловесный для API-only app  
❌ **Flask**: Нет built-in async support  
⚠️ **Node.js + Express**: Хороший вариант, но Python лучше для data processing

---

## 3. Database

### Decision: PostgreSQL 15 + Redis 7

**Chosen**: PostgreSQL as primary database, Redis for caching

**PostgreSQL Rationale**:
- **Relational Model**: Идеально для structured financial data
- **JSONB Support**: Для хранения raw responses от банков
- **Performance**: Отличные indexes, query optimization
- **Reliability**: ACID compliance critical для финансовых данных

**Redis Rationale**:
- **Caching**: Уменьшаем API calls к банкам
- **Session Storage**: JWT refresh tokens
- **Fast Lookups**: O(1) для ключевых операций

**Schema Highlights**:
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    transaction_id_from_bank VARCHAR(255) UNIQUE,
    date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id),
    transaction_type VARCHAR(20) CHECK (transaction_type IN ('income', 'expense')),
    raw_data JSONB, -- Original bank response
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_account_date ON transactions(account_id, date DESC);
CREATE INDEX idx_transactions_category ON transactions(category_id);
```

**Caching Strategy**:
```python
# Cache bank API responses for 1 hour
@cache(ttl=3600, key_prefix="accounts")
async def get_accounts_from_bank(bank_id: str, user_id: str):
    # Fetch from bank API
    pass

# Invalidate cache on manual sync
@invalidate_cache(key_prefix="accounts")
async def sync_accounts(bank_id: str, user_id: str):
    pass
```

### Alternatives Considered:

❌ **MongoDB**: NoSQL не нужен для structured financial data  
❌ **SQLite**: Не подходит для concurrent users  
⚠️ **MySQL**: Хороший вариант, но PostgreSQL JSONB support лучше

---

## 4. Frontend Framework

### Decision: React 18 + TypeScript + Vite

**Chosen**: React with TypeScript, built with Vite

**React Rationale**:
- **Component Reusability**: Dashboard widgets, charts, cards
- **Large Ecosystem**: Recharts для графиков, React Router для навигации
- **Performance**: Virtual DOM, lazy loading
- **Developer Experience**: Отличные dev tools

**TypeScript Rationale**:
- **Type Safety**: Catch errors at compile time
- **Better IDE Support**: Autocomplete, refactoring
- **Maintainability**: Self-documenting code

**Vite Rationale**:
- **Fast Dev Server**: HMR в milliseconds
- **Optimized Builds**: Tree-shaking, code splitting
- **Modern**: ESM support, no bundler overhead in dev

**Project Structure**:
```
src/
├── components/     # Reusable UI components
├── pages/          # Route-level components
├── services/       # API client layer
├── hooks/          # Custom React hooks
├── contexts/       # Global state (Auth, Theme)
└── types/          # TypeScript definitions
```

### Alternatives Considered:

❌ **Vue.js**: Меньше ecosystem для charts/visualization  
❌ **Angular**: Слишком тяжеловесный для MVP  
❌ **Next.js**: SSR не нужен для dashboard app  
⚠️ **SvelteKit**: Хороший вариант, но меньше community support

---

## 5. UI Framework

### Decision: TailwindCSS 3

**Chosen**: TailwindCSS for styling

**Rationale**:
- **Utility-First**: Rapid prototyping
- **Responsive**: Built-in breakpoints (sm, md, lg)
- **Customizable**: Easy to match design system
- **Performance**: PurgeCSS removes unused styles

**Example**:
```tsx
<div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
  <h3 className="text-xl font-bold text-gray-800 mb-2">
    Total Balance
  </h3>
  <p className="text-3xl font-extrabold text-green-600">
    {formatCurrency(totalBalance)}
  </p>
</div>
```

**Custom Theme**:
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#2563eb', // Blue for CTAs
        success: '#10b981', // Green for positive numbers
        danger: '#ef4444',  // Red for negative/warnings
      }
    }
  }
}
```

### Alternatives Considered:

❌ **Bootstrap**: Слишком opinionated, hard to customize  
❌ **Material-UI**: Тяжеловесный, React-specific lock-in  
⚠️ **ChakraUI**: Хороший вариант, но TailwindCSS более flexible

---

## 6. Charts Library

### Decision: Recharts 2

**Chosen**: Recharts for data visualization

**Rationale**:
- **React Native**: Built for React, not a wrapper
- **Composable**: Easy to build custom charts
- **Responsive**: Auto-resize on window changes
- **Lightweight**: Smaller bundle size than Chart.js

**Charts Used**:
1. **Pie Chart**: Spending by categories
2. **Line Chart**: Trends over time (income/expenses)
3. **Bar Chart**: Budget progress

**Example**:
```tsx
import { PieChart, Pie, Cell, Legend, Tooltip } from 'recharts';

const SpendingPieChart = ({ data }) => (
  <PieChart width={400} height={400}>
    <Pie
      data={data}
      dataKey="amount"
      nameKey="category"
      cx="50%"
      cy="50%"
      outerRadius={120}
      label
    >
      {data.map((entry, index) => (
        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
      ))}
    </Pie>
    <Tooltip formatter={(value) => formatCurrency(value)} />
    <Legend />
  </PieChart>
);
```

### Alternatives Considered:

❌ **Chart.js**: Not React-native, requires wrapper  
❌ **D3.js**: Too low-level, steep learning curve  
⚠️ **Victory**: Хороший вариант, но Recharts проще

---

## 7. Authentication & Security

### Decision: JWT + OAuth 2.0 + AES-256

**JWT for User Sessions**:
```python
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

**OAuth 2.0 Flow**:
1. User clicks "Connect VBank"
2. Backend generates OAuth URL: `https://ift.rtuitlab.dev/oauth/authorize?...`
3. User redirects to bank, authenticates
4. Bank redirects back with authorization code
5. Backend exchanges code for access_token
6. Backend encrypts and stores token

**Token Encryption** (AES-256):
```python
from cryptography.fernet import Fernet

cipher = Fernet(ENCRYPTION_KEY)

def encrypt_token(token: str) -> str:
    return cipher.encrypt(token.encode()).decode()

def decrypt_token(encrypted: str) -> str:
    return cipher.decrypt(encrypted.encode()).decode()
```

**Password Hashing**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### Security Checklist:

✅ Passwords hashed with bcrypt  
✅ JWT tokens with short expiration (30 min)  
✅ Refresh tokens for long sessions  
✅ Bank tokens encrypted at rest (AES-256)  
✅ HTTPS only in production  
✅ CORS configured properly  
✅ Rate limiting (100 req/min per user)  
✅ Input validation (Pydantic)

---

## 8. Categorization Algorithm

### Decision: Rule-Based Keyword Matching

**Chosen**: Simple rule-based алгоритм для MVP

**Algorithm**:
```python
CATEGORY_KEYWORDS = {
    "Продукты": ["перекресток", "metro", "магнит", "пятерочка", "ашан", "лента"],
    "Транспорт": ["яндекс такси", "uber", "метро", "мосгортранс", "rzd"],
    "Рестораны": ["макдональдс", "kfc", "burger king", "додо пицца", "starbucks"],
    "Развлечения": ["кинотеатр", "театр", "концерт", "музей", "steam", "netflix"],
    "Здоровье": ["аптека", "лекарство", "поликлиника", "медцентр"],
    "Одежда": ["zara", "h&m", "uniqlo", "спортмастер"],
    "Коммунальные": ["мосэнерго", "мосводоканал", "жку", "интернет", "связь"],
}

def categorize_transaction(description: str) -> str:
    description_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in description_lower for keyword in keywords):
            return category
    return "Прочее"
```

**Expected Accuracy**: 80-85% для русскоязычных транзакций

**Future Improvements**:
- Machine Learning (классификация текста)
- User feedback loop (manual recategorization)
- Merchant category codes (MCC) if available from bank

### Alternatives Considered:

❌ **ML Model**: Overengineering для MVP, нужны training data  
⚠️ **Merchant MCC Codes**: Идеально, но не все банки предоставляют

---

## 9. Background Jobs & Sync

### Decision: FastAPI BackgroundTasks + APScheduler

**Background Sync Strategy**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Sync all users' data every hour
@scheduler.scheduled_job('interval', hours=1)
async def sync_all_users():
    async for user in get_active_users():
        try:
            await sync_user_data(user.id)
        except Exception as e:
            logger.error(f"Sync failed for user {user.id}: {e}")

# Start scheduler
scheduler.start()
```

**Manual Sync** (on-demand):
```python
from fastapi import BackgroundTasks

@app.post("/accounts/sync")
async def manual_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    background_tasks.add_task(sync_user_data, current_user.id)
    return {"message": "Sync started in background"}
```

---

## 10. Error Handling & Retry Logic

### Decision: Exponential Backoff with httpx

**Retry Strategy**:
```python
from httpx import AsyncClient, HTTPStatusError
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_accounts_with_retry(bank_client, bank_token, consent_id):
    async with AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/accounts",
            headers={
                "Authorization": f"Bearer {bank_token}",
                "x-fapi-customer-consent-id": consent_id
            }
        )
        response.raise_for_status()
        return response.json()
```

**Error Response Format**:
```json
{
  "error": "BankAPIError",
  "message": "Failed to fetch accounts from VBank",
  "details": {
    "bank": "vbank",
    "status_code": 503,
    "retry_after": 60
  },
  "user_message": "Не удалось обновить данные из VBank. Показаны данные на 10:30"
}
```

---

## 11. PWA Configuration

### Decision: Vite PWA Plugin

**Manifest** (public/manifest.json):
```json
{
  "name": "FinanceHub",
  "short_name": "FinanceHub",
  "description": "Единый интерфейс финансового сервиса",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "icons": [
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Service Worker** (auto-generated by vite-plugin-pwa):
```typescript
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        // ... manifest config
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.financehub\.com\/.*$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 3600 // 1 hour
              }
            }
          }
        ]
      }
    })
  ]
})
```

---

## 12. Deployment Strategy

### Decision: Docker Compose (MVP), Kubernetes (Future)

**Docker Compose** (docker-compose.yml):
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: financehub
      POSTGRES_USER: financehub
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://financehub:${DB_PASSWORD}@postgres:5432/financehub
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "80:80"

volumes:
  postgres_data:
```

**Why Docker Compose**:
- ✅ Simple setup (1 command: `docker-compose up`)
- ✅ Reproducible environments
- ✅ Easy to share with judges
- ✅ Good enough for hackathon demo

**Future: Kubernetes**:
- Horizontal scaling (multiple backend pods)
- Auto-healing (pod restarts)
- Load balancing
- Secret management

---

## Performance Benchmarks

### Expected Performance:

| Metric | Target | Achieved (after optimization) |
|--------|--------|-------------------------------|
| API Response Time (p95) | < 200ms | TBD after implementation |
| Dashboard Load Time | < 2s | TBD after implementation |
| Concurrent Users | 100 | TBD after load testing |
| Transactions per Query | 1000 | TBD after optimization |
| Bank API Sync Time | < 5s | TBD after implementation |

### Optimization Strategies:

1. **Database Indexes**: На часто запрашиваемых полях
2. **Redis Caching**: Для bank API responses
3. **Lazy Loading**: В frontend (React.lazy, code splitting)
4. **Pagination**: Для списков транзакций (50 per page)
5. **Connection Pooling**: SQLAlchemy pool_size=20

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Backend** | FastAPI | 0.104+ | Async, type-safe, auto docs |
| **Language** | Python | 3.11+ | Performance + ecosystem |
| **Database** | PostgreSQL | 15 | Relational + JSONB support |
| **Cache** | Redis | 7 | Fast lookups, caching |
| **ORM** | SQLAlchemy | 2.0+ | Mature, async support |
| **Migrations** | Alembic | Latest | SQLAlchemy integration |
| **Auth** | python-jose | Latest | JWT implementation |
| **Password** | passlib | Latest | bcrypt hashing |
| **HTTP Client** | httpx | Latest | Async HTTP |
| **Frontend** | React | 18+ | Component-based UI |
| **Language** | TypeScript | 5+ | Type safety |
| **Build Tool** | Vite | 5+ | Fast dev server |
| **Styling** | TailwindCSS | 3+ | Utility-first |
| **Charts** | Recharts | 2+ | React-native charts |
| **Routing** | React Router | 6+ | Client-side routing |
| **HTTP Client** | Axios | Latest | Promise-based HTTP |
| **Deployment** | Docker | Latest | Containerization |
| **Orchestration** | Docker Compose | Latest | Multi-container |

---

**Next Steps**:
1. ✅ Technology research complete
2. ⏭️ Create detailed data model (data-model.md)
3. ⏭️ Define API contracts (contracts/api-spec.yaml)
4. ⏭️ Write quickstart guide (quickstart.md)
5. ⏭️ Generate tasks (/speckit.tasks)
6. ⏭️ Begin implementation (/speckit.implement)

