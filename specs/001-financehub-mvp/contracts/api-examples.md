# API Examples: FinanceHub MVP

**Date**: 2025-10-28  
**Base URL**: http://localhost:8000/api/v1

## Authentication

### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "Иван Иванов"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Иван Иванов",
  "created_at": "2025-10-28T10:30:00Z"
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## Banks

### Connect Bank (Initiate OAuth)

```http
GET /api/v1/banks/connect?bank_id=vbank
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "authorization_url": "https://ift.rtuitlab.dev/oauth/authorize?client_id=...&redirect_uri=...&state=..."
}
```

### OAuth Callback

```http
GET /api/v1/banks/callback?code=AUTH_CODE&state=STATE
```

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "bank_id": "vbank",
  "status": "active",
  "created_at": "2025-10-28T10:35:00Z"
}
```

## Accounts

### Get All Accounts

```http
GET /api/v1/accounts
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "total": 3,
  "accounts": [
    {
      "id": "account-123",
      "bank_name": "VBank",
      "account_type": "current",
      "balance": 125340.50,
      "currency": "RUB",
      "last_updated_at": "2025-10-28T10:30:00Z"
    },
    {
      "id": "account-456",
      "bank_name": "ABank",
      "account_type": "savings",
      "balance": 500000.00,
      "currency": "RUB",
      "last_updated_at": "2025-10-28T10:30:00Z"
    }
  ]
}
```

## Transactions

### Get Transactions

```http
GET /api/v1/transactions?date_from=2025-01-01&date_to=2025-10-28&limit=50&offset=0
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "total": 342,
  "offset": 0,
  "limit": 50,
  "transactions": [
    {
      "id": "txn-001",
      "account_id": "account-123",
      "date": "2025-10-27",
      "amount": 1250.00,
      "description": "Перекресток",
      "category": {
        "id": "cat-01",
        "name": "Продукты",
        "icon": "shopping-cart"
      },
      "transaction_type": "expense"
    }
  ]
}
```

## Analytics

### Get Spending by Categories

```http
GET /api/v1/analytics/spending?period=current_month
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "period": {
    "start": "2025-10-01",
    "end": "2025-10-31"
  },
  "total_spending": 45680.00,
  "categories": [
    {
      "category": "Продукты",
      "amount": 15340.00,
      "percentage": 33.6,
      "transaction_count": 42
    },
    {
      "category": "Транспорт",
      "amount": 8500.00,
      "percentage": 18.6,
      "transaction_count": 28
    }
  ]
}
```

## Budgets

### Get All Budgets

```http
GET /api/v1/budgets
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "budgets": [
    {
      "id": "budget-001",
      "category": {
        "id": "cat-01",
        "name": "Продукты"
      },
      "limit_amount": 15000.00,
      "spent_amount": 12340.00,
      "percentage_spent": 82.3,
      "status": "warning",
      "period_start": "2025-10-01",
      "period_end": "2025-10-31"
    }
  ]
}
```

---

For full OpenAPI specification, visit: http://localhost:8000/docs

