# FinanceHub MVP - Quickstart Guide

**Date**: 2025-10-28  
**Estimated Setup Time**: 15-20 minutes

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **Node.js 18+**: [Download](https://nodejs.org/)
- **PostgreSQL 15+**: [Download](https://www.postgresql.org/download/)
- **Redis 7+**: [Download](https://redis.io/download)
- **Docker & Docker Compose** (optional, for containerized setup): [Download](https://www.docker.com/products/docker-desktop)
- **Git**: [Download](https://git-scm.com/)

## Quick Start (Docker) - Recommended

**Fastest way to get started** - everything runs in containers:

```bash
# 1. Clone repository
git clone https://github.com/your-team/financehub.git
cd financehub

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your VTB API credentials
# VTB_TEAM_ID=team010-1
# VTB_TEAM_SECRET=<your-secret>

# 4. Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# 5. Run database migrations
docker-compose exec backend alembic upgrade head

# 6. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

That's it! FinanceHub is now running. 🎉

---

## Manual Setup (Development)

For development with hot reload:

### 1. Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# DATABASE_URL=postgresql://financehub:password@localhost:5432/financehub
# REDIS_URL=redis://localhost:6379/0
# SECRET_KEY=<generate-random-secret-key>
# VTB_TEAM_ID=team010-1
# VTB_TEAM_SECRET=<your-secret>

# Create PostgreSQL database
createdb financehub

# Run database migrations
alembic upgrade head

# Start backend server (with hot reload)
uvicorn app.main:app --reload --port 8000
```

Backend is now running at http://localhost:8000

### 2. Setup Frontend

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env
# VITE_API_BASE_URL=http://localhost:8000/api/v1

# Start frontend dev server (with hot reload)
npm run dev
```

Frontend is now running at http://localhost:3000

### 3. Verify Setup

Open browser and navigate to:
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs (Swagger UI)
- **Backend Health Check**: http://localhost:8000/health

---

## Configuration

### Environment Variables

#### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://financehub:password@localhost:5432/financehub
REDIS_URL=redis://localhost:6379/0

# JWT Authentication
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# VTB Open Banking API
VTB_API_BASE_URL=https://ift.rtuitlab.dev
VTB_TEAM_ID=team010-1
VTB_TEAM_SECRET=<your-secret-from-hackathon-platform>
VTB_OAUTH_CALLBACK=http://localhost:3000/callback

# Banks OAuth Clients
VBANK_CLIENT_ID=<will-be-provided>
ABANK_CLIENT_ID=<will-be-provided>
SBANK_CLIENT_ID=<will-be-provided>

# Encryption (for storing bank tokens)
ENCRYPTION_KEY=<generate-with-Fernet-generate_key>

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

**Generate SECRET_KEY**:
```bash
openssl rand -hex 32
```

**Generate ENCRYPTION_KEY**:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

#### Frontend (.env)

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000/api/v1

# OAuth Callback URL (must match backend config)
VITE_OAUTH_CALLBACK_URL=http://localhost:3000/callback

# App Config
VITE_APP_NAME=FinanceHub
VITE_APP_VERSION=1.0.0
```

---

## Database Migrations

### Create New Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column to users table"

# Review generated migration file in alembic/versions/
# Edit if necessary

# Apply migration
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all
alembic downgrade base
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_register_user
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

---

## Common Tasks

### Add New Category

```bash
# Connect to database
psql financehub

# Insert category
INSERT INTO categories (name, icon, keywords, category_type) 
VALUES ('Хобби', 'palette', ARRAY['рукоделие', 'творчество'], 'expense');
```

### Sync User Data Manually

```bash
# Use API endpoint
curl -X POST http://localhost:8000/api/v1/accounts/sync \
  -H "Authorization: Bearer <your-jwt-token>"
```

### View Logs

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Local logs
tail -f backend/logs/app.log
```

### Clear Cache

```bash
# Redis CLI
redis-cli

# Clear all cache
FLUSHALL

# Clear specific keys
KEYS accounts:*
DEL accounts:user-123
```

---

## Troubleshooting

### Backend won't start

**Error**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**: Ensure PostgreSQL is running
```bash
# Check PostgreSQL status
pg_ctl status

# Start PostgreSQL
pg_ctl start
```

### Frontend can't connect to backend

**Error**: `Network Error` or `CORS policy`

**Solution**: Check CORS configuration in backend `.env`
```env
CORS_ORIGINS=http://localhost:3000
```

### Database migrations fail

**Error**: `Target database is not up to date`

**Solution**: Check alembic version
```bash
# Check current version
alembic current

# Check migration history
alembic history

# Force upgrade
alembic stamp head
alembic upgrade head
```

### OAuth flow doesn't work

**Error**: `Invalid redirect_uri`

**Solution**: Ensure callback URL matches in both frontend and backend
- Backend `.env`: `VTB_OAUTH_CALLBACK=http://localhost:3000/callback`
- Frontend `.env`: `VITE_OAUTH_CALLBACK_URL=http://localhost:3000/callback`

---

## Production Deployment

### Build for Production

```bash
# Build backend Docker image
cd backend
docker build -t financehub-backend:latest .

# Build frontend Docker image
cd frontend
npm run build
docker build -t financehub-frontend:latest .
```

### Deploy with Docker Compose

```bash
# Production docker-compose.yml
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Environment Variables for Production

- Change `SECRET_KEY` to strong random value
- Use production PostgreSQL instance
- Enable HTTPS
- Set `LOG_LEVEL=WARNING`
- Configure monitoring and alerts

---

## Useful Commands

```bash
# Backend
uvicorn app.main:app --reload --port 8000  # Start dev server
alembic upgrade head                        # Run migrations
pytest --cov=app                            # Run tests with coverage
black app/                                  # Format code
flake8 app/                                 # Lint code

# Frontend
npm run dev                                 # Start dev server
npm run build                               # Build for production
npm run preview                             # Preview production build
npm test                                    # Run tests
npm run lint                                # Lint code

# Docker
docker-compose up -d                        # Start all services
docker-compose down                         # Stop all services
docker-compose logs -f <service>            # View logs
docker-compose exec <service> bash          # Enter container
docker-compose restart <service>            # Restart service

# Database
psql financehub                             # Connect to database
pg_dump financehub > backup.sql             # Backup database
psql financehub < backup.sql                # Restore database
```

---

## Next Steps

1. ✅ Setup complete
2. ⏭️ Register a test user at http://localhost:3000/register
3. ⏭️ Login and connect a bank (VBank/ABank/SBank)
4. ⏭️ View aggregated accounts and transactions
5. ⏭️ Explore analytics and budgets

---

## Support

- **Documentation**: See `README.md` and `specs/001-financehub-mvp/`
- **API Docs**: http://localhost:8000/docs
- **Issues**: Open an issue on GitHub
- **Contact**: team@financehub.ru

---

Happy coding! 🚀

