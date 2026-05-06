.PHONY: help test test-search test-backend test-frontend test-all test-performance test-quick test-prod run run-detached stop logs clean

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

help:
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(BLUE)IIIbrasil - Build & Test Commands$(NC)"
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make run              - Start services (foreground)"
	@echo "  make run-detached     - Start services (background)"
	@echo "  make stop             - Stop services"
	@echo "  make logs             - Show live logs"
	@echo "  make clean            - Stop & clean up"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test             - Run all tests"
	@echo "  make test-search      - Test search/query endpoints"
	@echo "  make test-backend     - Test backend only"
	@echo "  make test-frontend    - Test frontend only"
	@echo "  make test-quick       - Fast smoke tests"
	@echo "  make test-performance - Performance benchmarks"
	@echo "  make test-all         - Full test suite"
	@echo "  make test-prod        - Production readiness check"
	@echo ""
	@echo "$(GREEN)Build:$(NC)"
	@echo "  make build            - Build all Docker images"
	@echo "  make build-backend    - Build backend image"
	@echo "  make build-frontend   - Build frontend image"
	@echo ""
	@echo "$(GREEN)Deployment:$(NC)"
	@echo "  make validate         - Validate production setup"
	@echo "  make deploy           - Deploy to production"
	@echo ""

# ============================================================================
# DEVELOPMENT TARGETS
# ============================================================================

run:
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up

run-detached:
	@echo "$(BLUE)Starting services (background)...$(NC)"
	docker-compose up -d
	@sleep 5
	@echo "$(GREEN)✓ Services running$(NC)"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Health:   curl http://localhost:8000/health"

stop:
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose stop
	@echo "$(GREEN)✓ Services stopped$(NC)"

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

clean: stop
	@echo "$(BLUE)Cleaning up...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)✓ Cleaned up$(NC)"

# ============================================================================
# TESTING TARGETS
# ============================================================================

test: test-backend test-search
	@echo "$(GREEN)✓ All tests completed$(NC)"

test-backend:
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd backend && python -m pytest test_backend.py -v --tb=short

test-search:
	@echo "$(BLUE)Running search tests...$(NC)"
	@if [ -f backend/test_search.py ]; then \
		cd backend && python -m pytest test_search.py -v --tb=short; \
	else \
		echo "$(YELLOW)⚠ test_search.py not found$(NC)"; \
	fi

test-frontend:
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd frontend && npm run build

test-quick:
	@echo "$(BLUE)Running quick smoke tests...$(NC)"
	@bash scripts/test-search.sh http://localhost:8000 | head -50

test-performance:
	@echo "$(BLUE)Running performance benchmarks...$(NC)"
	cd backend && python -m pytest test_search.py::TestPerformance -v

test-all: test-backend test-search test-frontend
	@echo "$(GREEN)✓ Full test suite completed$(NC)"

test-prod:
	@echo "$(BLUE)Production readiness check...$(NC)"
	@bash scripts/production-check.sh

# ============================================================================
# BUILD TARGETS
# ============================================================================

build: build-backend build-frontend
	@echo "$(GREEN)✓ All images built$(NC)"

build-backend:
	@echo "$(BLUE)Building backend image...$(NC)"
	docker build -f backend/Dockerfile -t ebrasil-backend:latest backend/
	@echo "$(GREEN)✓ Backend image built$(NC)"

build-frontend:
	@echo "$(BLUE)Building frontend image...$(NC)"
	docker build -f frontend/Dockerfile -t ebrasil-frontend:latest frontend/
	@echo "$(GREEN)✓ Frontend image built$(NC)"

# ============================================================================
# VALIDATION TARGETS
# ============================================================================

validate:
	@echo "$(BLUE)Validating production setup...$(NC)"
	@bash scripts/production-check.sh

lint-backend:
	@echo "$(BLUE)Linting backend...$(NC)"
	cd backend && python -m pylint app/ --disable=all --enable=E,F --exit-zero

lint-frontend:
	@echo "$(BLUE)Linting frontend...$(NC)"
	cd frontend && npm run lint

format-backend:
	@echo "$(BLUE)Formatting backend...$(NC)"
	cd backend && python -m black app/

format-frontend:
	@echo "$(BLUE)Formatting frontend...$(NC)"
	cd frontend && npx prettier --write src/

# ============================================================================
# QUICK COMMANDS
# ============================================================================

health:
	@curl -s http://localhost:8000/health | jq '.'

curl-gastos:
	@curl -s "http://localhost:8000/api/v1/gastos?page_size=5" | jq '.'

curl-stats:
	@curl -s "http://localhost:8000/api/v1/stats/por-uf" | jq '.'

export-csv:
	@echo "$(BLUE)Exporting gastos to CSV...$(NC)"
	@curl -s "http://localhost:8000/api/v1/gastos/export/csv?page_size=100" > gastos_export.csv
	@echo "$(GREEN)✓ Exported to gastos_export.csv$(NC)"

# ============================================================================
# DATABASE TARGETS
# ============================================================================

db-migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	docker-compose exec backend python -m alembic upgrade head
	@echo "$(GREEN)✓ Migrations completed$(NC)"

db-seed:
	@echo "$(BLUE)Seeding database...$(NC)"
	docker-compose exec backend python -c "from app.seed import seed_if_empty; from app.database import SessionLocal; seed_if_empty(SessionLocal())"
	@echo "$(GREEN)✓ Database seeded$(NC)"

db-backup:
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	@docker-compose exec backend cp ebrasil.db /app/../backups/ebrasil_$$(date +%Y%m%d_%H%M%S).db.bak
	@echo "$(GREEN)✓ Database backed up$(NC)"

# ============================================================================
# DOCKER TARGETS
# ============================================================================

ps:
	docker-compose ps

shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

# ============================================================================
# DEPLOY TARGETS
# ============================================================================

deploy:
	@echo "$(BLUE)Deploying to production...$(NC)"
	@bash scripts/deploy.sh render
	@echo "$(GREEN)✓ Deployment initiated$(NC)"

deploy-aws:
	@echo "$(BLUE)Deploying to AWS...$(NC)"
	@bash scripts/deploy.sh aws

push-to-docker:
	@echo "$(BLUE)Pushing to Docker Hub...$(NC)"
	@docker tag ebrasil-backend:latest $(DOCKER_USER)/ebrasil-backend:latest
	@docker tag ebrasil-frontend:latest $(DOCKER_USER)/ebrasil-frontend:latest
	@docker push $(DOCKER_USER)/ebrasil-backend:latest
	@docker push $(DOCKER_USER)/ebrasil-frontend:latest
	@echo "$(GREEN)✓ Images pushed$(NC)"

# ============================================================================
# MONITORING & DEBUGGING
# ============================================================================

perf:
	@echo "$(BLUE)Checking performance...$(NC)"
	@ab -n 100 -c 10 -q http://localhost:8000/api/v1/gastos || echo "Install apache2-utils for ab"

monitor:
	@watch -n 1 'docker stats --no-stream'

debug:
	@echo "$(BLUE)Debug Info:$(NC)"
	@echo "Containers: $$(docker-compose ps -q | wc -l)"
	@echo "Backend health: $$(curl -s http://localhost:8000/health || echo 'DOWN')"
	@echo "Database: $$(docker-compose exec backend test -f ebrasil.db && echo 'EXISTS' || echo 'NOT FOUND')"

# ============================================================================
# GIT TARGETS
# ============================================================================

commit-all:
	@git add .
	@git commit -m "feat: production improvements"
	@git push origin main

version:
	@echo "Version 2.0.0 - Production Ready"

# ============================================================================
# DOCS TARGETS
# ============================================================================

docs:
	@echo "$(BLUE)Documentation$(NC)"
	@echo "  - START_HERE.md: Overview"
	@echo "  - PRODUCTION_QUICKSTART.md: 5-step guide"
	@echo "  - PRODUCTION_DEPLOYMENT.md: Full guide"
	@echo "  - TESTING_GUIDE.md: Testing procedures"
	@echo "  - SECURITY.md: Security guidelines"

open-docs:
	@open START_HERE.md 2>/dev/null || xdg-open START_HERE.md 2>/dev/null || code START_HERE.md

# ============================================================================
# CI/CD TARGETS
# ============================================================================

ci-test: test-all validate
	@echo "$(GREEN)✓ CI/CD checks passed$(NC)"

ci-build: build
	@echo "$(GREEN)✓ Build successful$(NC)"

# Default target
.DEFAULT_GOAL := help
