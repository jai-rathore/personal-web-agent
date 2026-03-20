.PHONY: help build run dev test clean deps install setup-gws

# Default target
help:
	@echo "Available commands:"
	@echo "  build      - Build all"
	@echo "  run        - Run the backend"
	@echo "  dev        - Run backend + frontend in dev mode"
	@echo "  test       - Run all tests"
	@echo "  clean      - Clean build artifacts"
	@echo "  deps       - Install all dependencies"
	@echo "  setup-gws  - Install gws CLI for Google Workspace tools"
	@echo ""
	@echo "Backend specific:"
	@echo "  build-api  - Install Python deps"
	@echo "  run-api    - Run the FastAPI backend (production mode)"
	@echo "  dev-api    - Run the FastAPI backend (hot-reload dev mode)"
	@echo "  test-api   - Run backend tests"
	@echo ""
	@echo "Frontend specific:"
	@echo "  build-web  - Build the frontend"
	@echo "  dev-web    - Run frontend dev server"
	@echo "  test-web   - Run frontend type check / lint"

# ── Build ─────────────────────────────────────────────────────────────────────

build: build-api build-web

build-api:
	@echo "Installing Python backend dependencies..."
	cd api && pip install -r requirements.txt

build-web:
	@echo "Building frontend..."
	cd web && npm run build

# ── Run ───────────────────────────────────────────────────────────────────────

run: run-api

run-api:
	@echo "Running backend (production)..."
	cd api && uvicorn app.main:app --host 0.0.0.0 --port $${PORT:-8080}

# ── Development ───────────────────────────────────────────────────────────────

dev:
	@echo "Starting development servers..."
	@echo "Backend:  http://localhost:8080"
	@echo "Frontend: http://localhost:5173"
	@make -j2 dev-api dev-web

dev-api:
	@echo "Running backend with hot-reload..."
	cd api && uvicorn app.main:app --host 0.0.0.0 --port $${PORT:-8080} --reload

dev-web:
	cd web && npm run dev

# ── Tests ─────────────────────────────────────────────────────────────────────

test: test-api test-web

test-api:
	@echo "Running backend tests..."
	cd api && python -m pytest tests/ -v

test-web:
	@echo "Running frontend checks..."
	cd web && npm run lint || true
	cd web && npm run type-check || npx tsc --noEmit || true

# ── Deps ──────────────────────────────────────────────────────────────────────

deps: deps-api deps-web

deps-api:
	@echo "Installing Python dependencies..."
	cd api && pip install -r requirements.txt

deps-web:
	@echo "Installing frontend dependencies..."
	cd web && npm ci

install: deps

# ── Google Workspace CLI ──────────────────────────────────────────────────────

setup-gws:
	@echo "Installing gws CLI (Google Workspace CLI)..."
	npm install -g @googleworkspace/cli
	@echo "Run 'gws auth setup' to authenticate with your Google account."

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	@echo "Cleaning..."
	rm -rf web/dist/ web/node_modules/
	find api -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find api -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find api -name "*.pyc" -delete 2>/dev/null || true

# ── Docker ────────────────────────────────────────────────────────────────────

docker-build:
	@echo "Building Docker image..."
	docker build -t personal-web-agent-api .

docker-run: docker-build
	@echo "Running Docker container..."
	docker run -p 8080:8080 --env-file .env personal-web-agent-api
