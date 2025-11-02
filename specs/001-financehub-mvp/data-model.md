# Data Model: FinanceHub MVP

**Date**: 2025-10-28  
**Database**: PostgreSQL 15  
**ORM**: SQLAlchemy 2.0

## Entity Relationship Diagram

```
User (1) ─────< BankConnection (N)
                    │
                    │ (1)
                    │
                    └─────< Account (N)
                                │
                                │ (1)
                                │
                                └─────< Transaction (N)
                                            │
                                            │ (N)
                                            │
                                        Category (1)

User (1) ─────< Budget (N) ──────> Category (1)
User (1) ─────< Goal (N)
User (1) ─────< Recommendation (N) ──────> BankProduct (0..1)
```

## Tables

### 1. users

Хранит информацию о пользователях системы.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'blocked', 'deleted')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
```

**Columns**:
- `id`: UUID primary key (auto-generated)
- `email`: User email (unique, used for login)
- `hashed_password`: bcrypt hashed password
- `full_name`: User's full name (optional)
- `status`: User account status (active/blocked/deleted)
- `created_at`: Registration timestamp
- `updated_at`: Last update timestamp

**Constraints**:
- Email must be unique and valid format
- Password must be hashed (never store plain text)
- Status must be one of: 'active', 'blocked', 'deleted'

---

### 2. bank_connections

Хранит подключения пользователей к банкам (OAuth tokens, consent info).

```sql
CREATE TABLE bank_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bank_id VARCHAR(50) NOT NULL CHECK (bank_id IN ('vbank', 'abank', 'sbank')),
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT,
    consent_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'revoked')),
    last_sync_at TIMESTAMP,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, bank_id)
);

CREATE INDEX idx_bank_connections_user ON bank_connections(user_id);
CREATE INDEX idx_bank_connections_status ON bank_connections(status);
CREATE INDEX idx_bank_connections_last_sync ON bank_connections(last_sync_at);
```

**Columns**:
- `id`: UUID primary key
- `user_id`: Foreign key to users table
- `bank_id`: Identifier банка ('vbank', 'abank', 'sbank')
- `encrypted_access_token`: AES-256 encrypted OAuth access token
- `encrypted_refresh_token`: AES-256 encrypted OAuth refresh token
- `consent_id`: Consent ID from bank (для API requests)
- `status`: Connection status (active/expired/revoked)
- `last_sync_at`: Timestamp последней синхронизации данных
- `token_expires_at`: Когда истекает access token
- `created_at`: When connection was created
- `updated_at`: Last update timestamp

**Constraints**:
- One user can connect to each bank only once (UNIQUE constraint)
- bank_id must be one of supported banks
- Tokens must be encrypted before storage

**Business Rules**:
- Tokens автоматически обновляются при истечении (через refresh token)
- При revocation статус меняется на 'revoked', токены удаляются
- last_sync_at обновляется после каждой успешной синхронизации

---

### 3. accounts

Хранит банковские счета и карты пользователей.

```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_connection_id UUID NOT NULL REFERENCES bank_connections(id) ON DELETE CASCADE,
    account_id_from_bank VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('current', 'savings', 'card', 'credit')),
    currency VARCHAR(3) DEFAULT 'RUB',
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    bank_name VARCHAR(100) NOT NULL,
    account_name VARCHAR(255),
    last_updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bank_connection_id, account_id_from_bank)
);

CREATE INDEX idx_accounts_bank_connection ON accounts(bank_connection_id);
CREATE INDEX idx_accounts_balance ON accounts(balance);
```

**Columns**:
- `id`: UUID primary key
- `bank_connection_id`: Foreign key to bank_connections table
- `account_id_from_bank`: Account ID from bank API (unique per connection)
- `account_type`: Type of account (current/savings/card/credit)
- `currency`: Currency code (ISO 4217, default RUB)
- `balance`: Current balance (2 decimal places)
- `bank_name`: Display name of bank ('VBank', 'ABank', 'SBank')
- `account_name`: User-friendly name (e.g., "Зарплатная карта")
- `last_updated_at`: When balance was last synced
- `created_at`: When account was first added
- `updated_at`: Last update timestamp

**Constraints**:
- Account ID from bank must be unique per connection
- Balance stored with 2 decimal precision
- Currency must be valid ISO 4217 code

**Business Rules**:
- Balance updates при каждой синхронизации
- account_name может быть задан пользователем (customization)
- При удалении bank_connection все accounts каскадно удаляются

---

### 4. categories

Справочник категорий расходов/доходов.

```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    icon VARCHAR(50),
    keywords TEXT[] DEFAULT '{}',
    category_type VARCHAR(20) DEFAULT 'expense' CHECK (category_type IN ('expense', 'income')),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_categories_name ON categories(name);
CREATE INDEX idx_categories_type ON categories(category_type);
```

**Columns**:
- `id`: UUID primary key
- `name`: Category name ('Продукты', 'Транспорт', etc.)
- `icon`: Icon identifier (e.g., 'shopping-cart', 'car')
- `keywords`: Array of keywords для автоматической категоризации
- `category_type`: Type (expense/income)
- `created_at`: When category was created

**Default Categories** (seed data):
```sql
INSERT INTO categories (name, icon, keywords, category_type) VALUES
    ('Продукты', 'shopping-cart', ARRAY['перекресток', 'metro', 'магнит', 'пятерочка', 'ашан', 'лента'], 'expense'),
    ('Транспорт', 'car', ARRAY['яндекс такси', 'uber', 'метро', 'мосгортранс', 'rzd'], 'expense'),
    ('Рестораны', 'restaurant', ARRAY['макдональдс', 'kfc', 'burger king', 'додо', 'starbucks'], 'expense'),
    ('Развлечения', 'gamepad', ARRAY['кинотеатр', 'театр', 'концерт', 'steam', 'netflix'], 'expense'),
    ('Здоровье', 'heart', ARRAY['аптека', 'лекарство', 'поликлиника', 'медцентр'], 'expense'),
    ('Одежда', 'tshirt', ARRAY['zara', 'h&m', 'uniqlo', 'спортмастер'], 'expense'),
    ('Коммунальные', 'home', ARRAY['мосэнерго', 'мосводоканал', 'жку', 'интернет'], 'expense'),
    ('Образование', 'book', ARRAY['университет', 'курсы', 'книги', 'udemy'], 'expense'),
    ('Прочее', 'dots', ARRAY[], 'expense'),
    ('Зарплата', 'dollar', ARRAY['зарплата', 'аванс', 'salary'], 'income'),
    ('Подработка', 'briefcase', ARRAY['фриланс', 'freelance', 'upwork'], 'income');
```

---

### 5. transactions

Хранит все финансовые транзакции пользователей из всех банков.

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    transaction_id_from_bank VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('income', 'expense')),
    currency VARCHAR(3) DEFAULT 'RUB',
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(account_id, transaction_id_from_bank)
);

CREATE INDEX idx_transactions_account_date ON transactions(account_id, date DESC);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_amount ON transactions(amount);
CREATE INDEX idx_transactions_date ON transactions(date DESC);
```

**Columns**:
- `id`: UUID primary key
- `account_id`: Foreign key to accounts table
- `transaction_id_from_bank`: Transaction ID from bank API (unique per account)
- `date`: Transaction date
- `amount`: Amount (positive for income, positive for expense too - type determines direction)
- `description`: Transaction description from bank
- `category_id`: Foreign key to categories table (auto-assigned)
- `transaction_type`: Type ('income' or 'expense')
- `currency`: Currency code
- `raw_data`: Original JSON response from bank (для debugging)
- `created_at`: When transaction was first imported
- `updated_at`: Last update timestamp

**Constraints**:
- Transaction ID from bank must be unique per account
- Amount stored with 2 decimal precision
- transaction_type must be 'income' or 'expense'

**Business Rules**:
- При import проверяем дубликаты по transaction_id_from_bank
- category_id присваивается автоматически categorization_service
- raw_data полезна для troubleshooting и аудита

**Query Patterns**:
```sql
-- Get transactions for dashboard (last 5)
SELECT * FROM transactions 
WHERE account_id IN (SELECT id FROM accounts WHERE bank_connection_id IN (...))
ORDER BY date DESC LIMIT 5;

-- Get transactions by category
SELECT category_id, SUM(amount) as total
FROM transactions
WHERE date BETWEEN '2024-01-01' AND '2024-12-31' AND transaction_type = 'expense'
GROUP BY category_id;

-- Get monthly trends
SELECT DATE_TRUNC('month', date) as month, SUM(amount) as total
FROM transactions
WHERE transaction_type = 'expense'
GROUP BY month
ORDER BY month DESC;
```

---

### 6. budgets

Хранит бюджеты пользователей по категориям.

```sql
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    limit_amount DECIMAL(15, 2) NOT NULL,
    spent_amount DECIMAL(15, 2) DEFAULT 0.00,
    period VARCHAR(20) DEFAULT 'monthly' CHECK (period IN ('monthly', 'yearly')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'on_track' CHECK (status IN ('on_track', 'warning', 'exceeded')),
    auto_created BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, category_id, period_start)
);

CREATE INDEX idx_budgets_user ON budgets(user_id);
CREATE INDEX idx_budgets_category ON budgets(category_id);
CREATE INDEX idx_budgets_period ON budgets(period_start, period_end);
CREATE INDEX idx_budgets_status ON budgets(status);
```

**Columns**:
- `id`: UUID primary key
- `user_id`: Foreign key to users table
- `category_id`: Foreign key to categories table
- `limit_amount`: Budget limit
- `spent_amount`: Amount spent so far (updated automatically)
- `period`: Period type ('monthly', 'yearly')
- `period_start`: Period start date
- `period_end`: Period end date
- `status`: Budget status ('on_track', 'warning', 'exceeded')
- `auto_created`: Was this budget auto-created by system?
- `created_at`: When budget was created
- `updated_at`: Last update timestamp

**Constraints**:
- One budget per (user, category, period_start) combination
- limit_amount must be positive
- spent_amount calculated автоматически from transactions

**Status Logic**:
```python
# on_track: < 80% spent
# warning: >= 80% and < 100% spent
# exceeded: >= 100% spent

def update_budget_status(budget):
    percentage = budget.spent_amount / budget.limit_amount * 100
    if percentage >= 100:
        budget.status = 'exceeded'
    elif percentage >= 80:
        budget.status = 'warning'
    else:
        budget.status = 'on_track'
```

**Business Rules**:
- spent_amount обновляется после каждой новой транзакции категории
- При auto_created=True бюджет создан на основе истории трат (среднее за 3 месяца)
- Notification отправляется при status='warning' or status='exceeded'

---

### 7. goals

Хранит финансовые цели пользователей.

```sql
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    target_amount DECIMAL(15, 2) NOT NULL,
    current_amount DECIMAL(15, 2) DEFAULT 0.00,
    target_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'achieved', 'archived')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_goals_user ON goals(user_id);
CREATE INDEX idx_goals_status ON goals(status);
```

**Columns**:
- `id`: UUID primary key
- `user_id`: Foreign key to users table
- `name`: Goal name (e.g., "Отпуск", "Новый ноутбук")
- `target_amount`: Target amount to save
- `current_amount`: Current progress
- `target_date`: Optional target date
- `status`: Goal status ('active', 'achieved', 'archived')
- `created_at`: When goal was created
- `updated_at`: Last update timestamp

**Business Rules**:
- current_amount обновляется вручную пользователем
- status автоматически меняется на 'achieved' when current_amount >= target_amount
- Мотивационные сообщения при 25%, 50%, 75%, 100%

---

### 8. bank_products

Справочник банковских продуктов (для рекомендаций и сравнения).

```sql
CREATE TABLE bank_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_name VARCHAR(100) NOT NULL,
    product_type VARCHAR(50) NOT NULL CHECK (product_type IN ('deposit', 'credit', 'card', 'loan')),
    name VARCHAR(255) NOT NULL,
    interest_rate DECIMAL(5, 2),
    term_months INTEGER,
    min_amount DECIMAL(15, 2),
    max_amount DECIMAL(15, 2),
    description TEXT,
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bank_products_type ON bank_products(product_type);
CREATE INDEX idx_bank_products_bank ON bank_products(bank_name);
CREATE INDEX idx_bank_products_rate ON bank_products(interest_rate DESC);
```

**Columns**:
- `id`: UUID primary key
- `bank_name`: Bank name ('VBank', 'ABank', 'SBank')
- `product_type`: Product type ('deposit', 'credit', 'card', 'loan')
- `name`: Product name
- `interest_rate`: Interest rate (e.g., 18.50 for 18.5%)
- `term_months`: Term in months (для вкладов, кредитов)
- `min_amount`: Minimum amount
- `max_amount`: Maximum amount (для кредитов)
- `description`: Product description
- `url`: Link to product page (партнерская ссылка)
- `created_at`: When product was added
- `updated_at`: Last update timestamp

**Data Source**: Products API от банков (синхронизируется периодически)

---

### 9. recommendations

Хранит персонализированные рекомендации для пользователей.

```sql
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('insight', 'product', 'saving_tip', 'warning')),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'viewed', 'dismissed')),
    bank_product_id UUID REFERENCES bank_products(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_recommendations_user ON recommendations(user_id);
CREATE INDEX idx_recommendations_status ON recommendations(status);
CREATE INDEX idx_recommendations_priority ON recommendations(priority DESC);
CREATE INDEX idx_recommendations_created ON recommendations(created_at DESC);
```

**Columns**:
- `id`: UUID primary key
- `user_id`: Foreign key to users table
- `type`: Recommendation type ('insight', 'product', 'saving_tip', 'warning')
- `title`: Recommendation title
- `description`: Detailed description
- `priority`: Priority (1=lowest, 10=highest)
- `status`: Status ('new', 'viewed', 'dismissed')
- `bank_product_id`: Optional link to bank product (для product recommendations)
- `created_at`: When recommendation was generated
- `expires_at`: Optional expiration date

**Recommendation Types**:
- **insight**: "Вы тратите на рестораны на 30% больше, чем в прошлом месяце"
- **product**: "В SBank вклад под 18% — выгоднее вашего на 3%"
- **saving_tip**: "Можете сэкономить 2,000₽/мес, отменив неиспользуемые подписки"
- **warning**: "Превышен бюджет на Рестораны на 5,000₽"

**Business Rules**:
- Recommendations генерируются recommendation_service
- priority определяет порядок отображения
- expires_at для time-sensitive рекомендаций (например, акции)
- Dismissed recommendations не показываются снова

---

## Migrations (Alembic)

### Initial Migration

```python
# alembic/versions/001_initial_schema.py

def upgrade():
    # Create tables in dependency order
    op.create_table('users', ...)
    op.create_table('categories', ...)
    op.create_table('bank_connections', ...)
    op.create_table('accounts', ...)
    op.create_table('transactions', ...)
    op.create_table('budgets', ...)
    op.create_table('goals', ...)
    op.create_table('bank_products', ...)
    op.create_table('recommendations', ...)
    
    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    # ... more indexes
    
    # Seed default categories
    op.execute("""
        INSERT INTO categories (name, icon, keywords, category_type) VALUES
        ('Продукты', 'shopping-cart', ARRAY['перекресток', 'metro'], 'expense'),
        ...
    """)

def downgrade():
    op.drop_table('recommendations')
    op.drop_table('bank_products')
    op.drop_table('goals')
    op.drop_table('budgets')
    op.drop_table('transactions')
    op.drop_table('accounts')
    op.drop_table('bank_connections')
    op.drop_table('categories')
    op.drop_table('users')
```

---

## SQLAlchemy Models Example

```python
# app/models/transaction.py

from sqlalchemy import Column, String, Numeric, Date, ForeignKey, Text, Enum, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    transaction_id_from_bank = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"))
    transaction_type = Column(Enum("income", "expense", name="transaction_type_enum"), nullable=False)
    currency = Column(String(3), default="RUB")
    raw_data = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default="NOW()")
    updated_at = Column(TIMESTAMP, server_default="NOW()", onupdate="NOW()")
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    
    __table_args__ = (
        UniqueConstraint("account_id", "transaction_id_from_bank", name="uq_account_transaction"),
        Index("idx_transactions_account_date", "account_id", "date"),
        Index("idx_transactions_category", "category_id"),
    )
```

---

## Query Optimization Tips

1. **Use indexes**: All foreign keys and frequently filtered columns indexed
2. **Pagination**: Always paginate large result sets
3. **Select only needed columns**: Use `query.options(load_only(...))`
4. **Eager loading**: Use `joinedload()` to avoid N+1 queries
5. **Aggregate at DB level**: Use `GROUP BY` for analytics, not in-memory
6. **Cache frequently accessed data**: Use Redis for categories, etc.

---

**Next Steps**:
1. ✅ Data model defined
2. ⏭️ Create API contracts (contracts/api-spec.yaml)
3. ⏭️ Write quickstart guide (quickstart.md)
4. ⏭️ Generate tasks (/speckit.tasks)
5. ⏭️ Begin implementation (/speckit.implement)

