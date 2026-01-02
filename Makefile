# =============================================================================
# Synkventory Makefile
# =============================================================================
# Common commands for development and deployment
#
# Usage:
#   make <target>
#
# Examples:
#   make dev           - Start development environment
#   make migrate-up    - Run all pending migrations
#   make migrate-create name=add_users_table
# =============================================================================

.PHONY: help dev dev-build dev-down dev-logs \
        migrate-up migrate-down migrate-create migrate-history migrate-current \
        prod prod-build prod-down \
        do-build do-push do-deploy \
        test lint format clean

# Default target
help:
	@echo "Synkventory Development Commands"
	@echo "================================"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start development environment"
	@echo "  make dev-build        - Build and start development environment"
	@echo "  make dev-down         - Stop development environment"
	@echo "  make dev-logs         - View development logs"
	@echo ""
	@echo "Database Migrations:"
	@echo "  make migrate-up       - Run all pending migrations"
	@echo "  make migrate-down     - Rollback last migration"
	@echo "  make migrate-create name=xxx  - Create new migration"
	@echo "  make migrate-history  - Show migration history"
	@echo "  make migrate-current  - Show current migration version"
	@echo ""
	@echo "Production:"
	@echo "  make prod             - Start production environment"
	@echo "  make prod-build       - Build and start production environment"
	@echo "  make prod-down        - Stop production environment"
	@echo ""
	@echo "Digital Ocean:"
	@echo "  make do-build         - Build production Docker images"
	@echo "  make do-push          - Push images to DO Container Registry"
	@echo "  make do-deploy        - Deploy to DO App Platform"
	@echo ""
	@echo "Code Quality:"
	@echo "  make test             - Run tests"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Remove containers, volumes, and cache"

# =============================================================================
# Development Commands
# =============================================================================

dev:
	docker-compose up -d

dev-build:
	docker-compose up -d --build

dev-down:
	docker-compose down

dev-logs:
	docker-compose logs -f

# =============================================================================
# Database Migration Commands
# =============================================================================

# Run all pending migrations
migrate-up:
	docker-compose exec backend alembic upgrade head

# Rollback the last migration
migrate-down:
	docker-compose exec backend alembic downgrade -1

# Create a new migration
# Usage: make migrate-create name=add_users_table
migrate-create:
ifndef name
	$(error name is required. Usage: make migrate-create name=your_migration_name)
endif
	docker-compose exec backend alembic revision --autogenerate -m "$(name)"

# Show migration history
migrate-history:
	docker-compose exec backend alembic history --verbose

# Show current migration version
migrate-current:
	docker-compose exec backend alembic current

# Upgrade to a specific revision
# Usage: make migrate-to rev=abc123
migrate-to:
ifndef rev
	$(error rev is required. Usage: make migrate-to rev=revision_id)
endif
	docker-compose exec backend alembic upgrade $(rev)

# Generate SQL for migrations (useful for review)
# Usage: make migrate-sql
migrate-sql:
	docker-compose exec backend alembic upgrade head --sql

# =============================================================================
# Production Commands
# =============================================================================

prod:
	docker-compose -f docker-compose.prod.yml up -d

prod-build:
	docker-compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

# Run migrations in production
prod-migrate:
	docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# =============================================================================
# Digital Ocean Deployment Commands
# =============================================================================

# Configuration - override these with environment variables
DO_REGISTRY ?= registry.digitalocean.com/synkventory
VERSION ?= latest

# Build production images
do-build:
	@echo "Building production images..."
	docker build -t $(DO_REGISTRY)/synkventory-backend:$(VERSION) -f backend/Dockerfile.prod backend/
	docker build -t $(DO_REGISTRY)/synkventory-frontend:$(VERSION) -f frontend/Dockerfile.prod frontend/
	@echo "Build complete!"

# Push images to Digital Ocean Container Registry
do-push: do-build
	@echo "Pushing images to DO Container Registry..."
	docker push $(DO_REGISTRY)/synkventory-backend:$(VERSION)
	docker push $(DO_REGISTRY)/synkventory-frontend:$(VERSION)
	@echo "Push complete!"

# Deploy to Digital Ocean App Platform
do-deploy:
	@echo "Deploying to Digital Ocean App Platform..."
	doctl apps create --spec .do/app.yaml
	@echo "Deployment initiated!"

# Update existing DO App Platform deployment
do-update:
ifndef APP_ID
	$(error APP_ID is required. Usage: make do-update APP_ID=your-app-id)
endif
	@echo "Updating Digital Ocean App Platform deployment..."
	doctl apps update $(APP_ID) --spec .do/app.yaml
	@echo "Update initiated!"

# Start production with DO compose file
do-compose:
	docker-compose -f docker-compose.digitalocean.yml up -d

do-compose-build:
	docker-compose -f docker-compose.digitalocean.yml up -d --build

do-compose-down:
	docker-compose -f docker-compose.digitalocean.yml down

# =============================================================================
# Code Quality Commands
# =============================================================================

test:
	docker-compose exec backend pytest -v

lint:
	docker-compose exec backend ruff check app/

format:
	docker-compose exec backend ruff format app/

# =============================================================================
# Local Development (without Docker)
# =============================================================================

# Run migrations locally (requires .env to be configured)
local-migrate-up:
	cd backend && alembic upgrade head

local-migrate-down:
	cd backend && alembic downgrade -1

local-migrate-create:
ifndef name
	$(error name is required. Usage: make local-migrate-create name=your_migration_name)
endif
	cd backend && alembic revision --autogenerate -m "$(name)"

# =============================================================================
# Cleanup Commands
# =============================================================================

clean:
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true

# Remove only Docker volumes (careful - this deletes database data!)
clean-volumes:
	docker-compose down -v
	docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
