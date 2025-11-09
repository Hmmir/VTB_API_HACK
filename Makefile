.PHONY: help build up down restart logs reset-env seed-data test lint clean verify-gost demo

help: ## Show this help message
	@echo "🏦 VTB API Hackathon - Family Banking Hub"
	@echo "=================================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "📱 Frontend: http://localhost"
	@echo "🔧 Backend API: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart
	@echo "✅ Services restarted!"

logs: ## Show logs for all services
	docker-compose logs -f

logs-backend: ## Show backend logs only
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs only
	docker-compose logs -f frontend

reset-env: ## Reset environment (clean database, rebuild)
	@echo "⚠️  This will delete all data! Press Ctrl+C to cancel, or Enter to continue..."
	@read
	docker-compose down -v
	docker-compose build
	docker-compose up -d
	@echo "⏳ Waiting for database..."
	@sleep 10
	docker-compose exec backend alembic upgrade head
	@echo "✅ Environment reset complete!"

seed-data: ## Seed demo data
	docker-compose exec backend python scripts/create_demo_user.py
	docker-compose exec backend python scripts/create_team_clients.py
	docker-compose exec backend python scripts/seed_family_demo.py
	@echo "✅ Demo data seeded!"

test: ## Run backend tests
	docker-compose exec backend pytest -v

lint: ## Run linters
	docker-compose exec backend black app/ --check
	docker-compose exec backend flake8 app/
	docker-compose exec frontend npm run lint

clean: ## Clean up Docker resources
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete!"

verify-gost: ## Verify GOST integration
	docker-compose exec backend python scripts/verify_gost.py

demo: ## Prepare for demo (reset + seed)
	@echo "🎬 Preparing demo environment..."
	@make reset-env
	@make seed-data
	@echo ""
	@echo "✅ Demo ready!"
	@echo "📝 Login credentials:"
	@echo "   Demo user: demo / password"
	@echo "   Team user: team075-1 / password"
	@echo ""
	@echo "🔗 Links:"
	@echo "   Frontend: http://localhost"
	@echo "   API Docs: http://localhost:8000/docs"

status: ## Check service status
	@echo "📊 Service Status:"
	@docker-compose ps

db-shell: ## Open database shell
	docker-compose exec db psql -U postgres -d financehub

backend-shell: ## Open backend shell
	docker-compose exec backend /bin/bash

frontend-shell: ## Open frontend shell
	docker-compose exec frontend /bin/sh

migrations: ## Run database migrations
	docker-compose exec backend alembic upgrade head

create-migration: ## Create new migration (usage: make create-migration MSG="description")
	docker-compose exec backend alembic revision --autogenerate -m "$(MSG)"

quick-start: ## Quick start for new users
	@echo "🚀 Quick Start - Family Banking Hub"
	@echo "=================================="
	@echo ""
	@echo "1️⃣  Building containers..."
	@make build
	@echo ""
	@echo "2️⃣  Starting services..."
	@make up
	@echo ""
	@echo "3️⃣  Running migrations..."
	@sleep 10
	@make migrations
	@echo ""
	@echo "4️⃣  Seeding demo data..."
	@make seed-data
	@echo ""
	@echo "✅ Setup complete! Open http://localhost"
	@echo "📝 Login: demo / password"

backup-db: ## Backup database
	docker-compose exec db pg_dump -U postgres financehub > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up!"

restore-db: ## Restore database from backup (usage: make restore-db FILE=backup.sql)
	@test -n "$(FILE)" || (echo "❌ Error: FILE parameter required" && exit 1)
	docker-compose exec -T db psql -U postgres financehub < $(FILE)
	@echo "✅ Database restored from $(FILE)"

healthcheck: ## Check API health
	@echo "🏥 Health Check"
	@echo "==============="
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ Backend not responding"
	@echo ""
	@curl -s http://localhost:8000/api/v1/system/info | python -m json.tool || echo "❌ API not responding"

gost-status: ## Check GOST status
	@curl -s http://localhost:8000/api/v1/system/gost-status | python -m json.tool

jury-demo: ## Prepare for jury demonstration
	@echo "🏆 Preparing for Jury Demo..."
	@echo "=============================="
	@echo ""
	@make demo
	@echo ""
	@echo "✅ Ready for jury demonstration!"
	@echo ""
	@echo "📋 Demo Checklist:"
	@echo "  ✅ Services running"
	@echo "  ✅ Demo data seeded"
	@echo "  ✅ Frontend accessible"
	@echo "  ✅ Backend API ready"
	@echo ""
	@echo "🎬 Demo Script:"
	@echo "  1. Open http://localhost"
	@echo "  2. Login with: demo / password"
	@echo "  3. Show multi-bank dashboard"
	@echo "  4. Create family group"
	@echo "  5. Show AI insights"
	@echo "  6. Demonstrate GOST status"
	@echo ""
	@echo "🔍 Verification:"
	@make verify-gost







