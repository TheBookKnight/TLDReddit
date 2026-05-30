.PHONY: help install dev test lint build docker-up docker-down docker-build clean

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Install ───────────────────────────────────────────────────────────────────

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies (requires uv)
	cd backend && uv sync --extra dev

install-frontend: ## Install frontend dependencies
	cd frontend && npm ci

# ── Development ───────────────────────────────────────────────────────────────

dev: ## Start both backend and frontend dev servers
	@echo "Starting backend and frontend..."
	@trap 'kill 0' SIGINT; \
	  cd backend && uv run uvicorn src.main:app --reload --port 8000 & \
	  cd frontend && npm run dev & \
	  wait

dev-backend: ## Start backend dev server only
	cd backend && uv run uvicorn src.main:app --reload --port 8000

dev-frontend: ## Start frontend dev server only
	cd frontend && npm run dev

# ── Testing ───────────────────────────────────────────────────────────────────

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests with coverage
	cd backend && uv run python -m pytest --cov=src --cov-report=term-missing -v

test-frontend: ## Run frontend tests
	cd frontend && npm test

test-coverage: ## Run all tests with coverage reports
	cd backend && uv run python -m pytest --cov=src --cov-report=html --cov-report=term-missing
	cd frontend && npm run test:coverage

# ── Linting & Type Checking ───────────────────────────────────────────────────

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Run ruff and mypy on backend
	cd backend && uv run ruff check src tests
	cd backend && uv run mypy src

lint-frontend: ## Run ESLint and TypeScript check on frontend
	cd frontend && npm run lint
	cd frontend && npx tsc --noEmit

format: ## Auto-format backend code with ruff
	cd backend && uv run ruff check --fix src tests
	cd backend && uv run ruff format src tests

# ── Docker ────────────────────────────────────────────────────────────────────

docker-build: ## Build Docker images
	docker compose build

docker-up: ## Start all services with Docker Compose
	docker compose up -d

docker-down: ## Stop all Docker Compose services
	docker compose down

docker-logs: ## Follow Docker Compose logs
	docker compose logs -f

docker-restart: ## Restart Docker Compose services
	docker compose restart

# ── Database ──────────────────────────────────────────────────────────────────

db-reset: ## Remove local SQLite database (dev only)
	rm -f backend/tldreddit.db

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	rm -rf backend/.mypy_cache backend/.ruff_cache backend/htmlcov backend/.pytest_cache
	rm -rf frontend/dist frontend/coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
