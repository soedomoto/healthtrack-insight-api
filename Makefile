include .env
export

.PHONY: help install dev run test lint format clean db-up db-down db-dev db-seed db-migration db-migrate-upgrade db-migrate-downgrade

help:
	@echo "HealthTrack API - Available Commands"
	@echo "===================================="
	@echo "Setup & Installation:"
	@echo "  make install              - Install dependencies"
	@echo "  make dev                  - Run development server"
	@echo ""
	@echo "Database:"
	@echo "  make db-up                - Start database containers"
	@echo "  make db-down              - Stop database containers"
	@echo "  make db-dev               - Set up development database (create + migrate + seed)"
	@echo "  make db-seed              - Seed database with sample data"
	@echo "  make db-migration         - Create new migration"
	@echo "  make db-migrate-upgrade   - Apply pending migrations"
	@echo "  make db-migrate-downgrade - Rollback last migration"
	@echo "  make db-current           - Show current migration version"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test                 - Run tests"
	@echo "  make lint                 - Run linters (flake8, mypy)"
	@echo "  make format               - Format code (black, isort)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                - Remove cache and build files"

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

dev:
	. .venv/bin/activate && uvicorn app.main:app --reload --host $(API_HOST) --port $(API_PORT) --env-file .env

db-up:
	docker-compose --env-file .env up -d

db-down:
	docker-compose --env-file .env down

db-dev: db-up db-migrate-upgrade db-seed
	@echo "✓ Database setup complete"

db-seed:
	. .venv/bin/activate && python scripts/seed_db.py

db-migration:
	@migration_name="$(filter-out $@,$(MAKECMDGOALS))"; \
	if [ -z "$$migration_name" ]; then \
		read -p "Enter migration name: " migration_name; \
	fi; \
	. .venv/bin/activate && ALEMBIC_SQLALCHEMY_URL="$${DATABASE_URL}" alembic -c migrations/alembic.ini revision --autogenerate -m "$$migration_name"

db-migrate-upgrade:
	. .venv/bin/activate && alembic -c migrations/alembic.ini upgrade head

db-migrate-downgrade:
	. .venv/bin/activate && alembic -c migrations/alembic.ini downgrade -1

db-current:
	. .venv/bin/activate && alembic -c migrations/alembic.ini current

test:
	. .venv/bin/activate && pytest -v

lint:
	. .venv/bin/activate && flake8 app/ && mypy app/

format:
	. .venv/bin/activate && black app/ && isort app/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ build/ dist/ *.egg-info/
	@echo "✓ Cleaned up cache and build files"

# Catch-all rule to prevent Make from treating extra arguments as targets
%:
	@:
