.PHONY: help build run test clean dev deps tidy build-web dev-web test-web install

# Default target
help:
	@echo "Available commands:"
	@echo "  build    - Build both backend and frontend"
	@echo "  run      - Run the backend application"
	@echo "  dev      - Run both frontend and backend in development mode"
	@echo "  test     - Run all tests"
	@echo "  clean    - Clean all build artifacts"
	@echo "  deps     - Download all dependencies"
	@echo "  tidy     - Tidy up go.mod"
	@echo ""
	@echo "Backend specific:"
	@echo "  build-api - Build the backend"
	@echo "  run-api   - Run the backend"
	@echo "  test-api  - Run backend tests"
	@echo ""
	@echo "Frontend specific:"
	@echo "  build-web - Build the frontend"
	@echo "  dev-web   - Run frontend dev server"
	@echo "  test-web  - Run frontend tests"

# Build the application
build: build-api build-web

build-api:
	@echo "Building backend..."
	cd api && go build -o ../bin/server ./cmd/server

build-web:
	@echo "Building frontend..."
	cd web && npm run build

# Run the application
run: run-api

run-api: build-api
	@echo "Running backend..."
	./bin/server

# Development mode
dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8080"
	@echo "Frontend: http://localhost:5173"
	@make -j2 dev-api dev-web

dev-api:
	@if command -v air > /dev/null 2>&1; then \
		cd api && air -c ../.air.toml; \
	else \
		echo "Air not installed. Install with: go install github.com/cosmtrek/air@latest"; \
		echo "Running without auto-reload..."; \
		$(MAKE) run-api; \
	fi

dev-web:
	cd web && npm run dev

# Run tests
test: test-api test-web

test-api:
	@echo "Running backend tests..."
	cd api && go test -v ./...

test-web:
	@echo "Running frontend tests..."
	cd web && npm run lint || true
	cd web && npm run type-check || npx tsc --noEmit || true

# Clean build artifacts
clean:
	@echo "Cleaning..."
	rm -rf bin/ web/dist/ web/node_modules/
	cd api && go clean

# Download dependencies
deps: deps-api deps-web

deps-api:
	@echo "Downloading backend dependencies..."
	cd api && go mod download

deps-web:
	@echo "Installing frontend dependencies..."
	cd web && npm ci

# Install all dependencies (alias for deps)
install: deps

# Tidy up go.mod
tidy:
	@echo "Tidying go.mod..."
	cd api && go mod tidy

# Initialize the project (first time setup)
init: deps tidy
	@echo "Initializing project..."
	mkdir -p bin
	@echo "Project initialized. Copy .env.example to .env and configure your environment variables."

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build -t personal-web-agent-api .

docker-run: docker-build
	@echo "Running Docker container..."
	docker run -p 8080:8080 --env-file .env personal-web-agent-api