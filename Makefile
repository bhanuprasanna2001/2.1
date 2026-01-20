# =============================================================================
# Bookmark Manager REST API - Makefile for Development Tasks
# =============================================================================
# Usage:
#   make help       - Show available commands
#   make check      - Run all quality checks
#   make fix        - Auto-fix all fixable issues
#   make test       - Run tests with coverage
#   make db-up      - Start PostgreSQL in Docker
#   make dev        - Run development server
# =============================================================================

.PHONY: help install dev-install run dev db-up db-down db-logs \
        migrate migrate-down migrate-create lint format fix typecheck \
        test test-cov check clean docker-build docker-run

# Default target
help:
	@echo ""
	@echo "Bookmark Manager API - Development Commands"
	@echo "============================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run           - Run the API server"
	@echo "  make dev           - Run with auto-reload"
	@echo ""
	@echo "Database:"
	@echo "  make db-up         - Start PostgreSQL container"
	@echo "  make db-down       - Stop PostgreSQL container"
	@echo "  make db-logs       - View PostgreSQL logs"
	@echo "  make migrate       - Run database migrations"
	@echo "  make migrate-down  - Rollback last migration"
	@echo "  make migrate-create MSG=desc - Create new migration"
	@echo ""
	@echo "Quality Checks:"
	@echo "  make lint          - Run Ruff linter"
	@echo "  make format        - Check code formatting"
	@echo "  make typecheck     - Run mypy type checker"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make check         - Run ALL quality checks"
	@echo ""
	@echo "Auto-Fix:"
	@echo "  make fix           - Auto-fix lint + format issues"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run full stack with Docker Compose"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Remove cache files"
	@echo ""

# =============================================================================
# Setup
# =============================================================================
install:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Installing dependencies"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	pip install -e .
	@echo "✓ Installation complete\n"

dev-install:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Installing development dependencies"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	pip install -e ".[dev]"
	@echo "✓ Development installation complete\n"

# =============================================================================
# Development Server
# =============================================================================
run:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Starting API server"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Starting development server with auto-reload"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# =============================================================================
# Database Commands
# =============================================================================
db-up:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Starting PostgreSQL container"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	docker compose up -d db
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	@echo "✓ PostgreSQL is running on localhost:5433\n"

db-down:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Stopping PostgreSQL container"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	docker compose down
	@echo "✓ PostgreSQL stopped\n"

db-logs:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ PostgreSQL container logs"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	docker compose logs -f db

db-shell:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Connecting to PostgreSQL shell"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	docker exec -it bookmark_db psql -U bookmark_user -d bookmark_db

# =============================================================================
# Migrations
# =============================================================================
migrate:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Running database migrations"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	alembic upgrade head
	@echo "✓ Migrations complete\n"

migrate-down:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Rolling back last migration"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	alembic downgrade -1
	@echo "✓ Rollback complete\n"

migrate-create:
ifndef MSG
	$(error MSG is required. Usage: make migrate-create MSG="description")
endif
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Creating new migration: $(MSG)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	alembic revision --autogenerate -m "$(MSG)"
	@echo "✓ Migration created\n"

migrate-history:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Migration history"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	alembic history --verbose

# =============================================================================
# Quality Checks
# =============================================================================
lint:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Running Ruff linter"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	python -m ruff check app tests
	@echo "✓ Linting passed\n"

format:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Checking code formatting"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	python -m ruff format --check app tests
	@echo "✓ Formatting check passed\n"

typecheck:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Running mypy type checker"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	python -m mypy app
	@echo "✓ Type checking passed\n"

check: lint format typecheck
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✓ All quality checks passed!"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# =============================================================================
# Auto-Fix
# =============================================================================
fix:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Auto-fixing lint issues"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	python -m ruff check --fix app tests
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Auto-formatting code"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	python -m ruff format app tests
	@echo "✓ All fixes applied\n"

# =============================================================================
# Testing
# =============================================================================
test:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Running tests"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	python -m pytest tests/ -v
	@echo "✓ Tests complete\n"

test-cov:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Running tests with coverage"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
	@echo "✓ Coverage report generated in htmlcov/\n"

# =============================================================================
# Docker
# =============================================================================
docker-build:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Building Docker image"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	docker compose build
	@echo "✓ Docker image built\n"

docker-run:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Starting full stack with Docker Compose"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	docker compose up -d
	@echo "✓ Stack is running"
	@echo "  API: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs\n"

docker-down:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Stopping Docker Compose stack"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	docker compose down
	@echo "✓ Stack stopped\n"

# =============================================================================
# Cleanup
# =============================================================================
clean:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶ Cleaning up cache files"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleanup complete\n"
