.PHONY: help build run test clean dev deps tidy

# Default target
help:
	@echo "Available commands:"
	@echo "  build    - Build the application"
	@echo "  run      - Run the application"
	@echo "  dev      - Run in development mode with auto-reload"
	@echo "  test     - Run tests"
	@echo "  clean    - Clean build artifacts"
	@echo "  deps     - Download dependencies"
	@echo "  tidy     - Tidy up go.mod"

# Build the application
build:
	@echo "Building application..."
	cd api && go build -o ../bin/server ./cmd/server

# Run the application
run: build
	@echo "Running application..."
	./bin/server

# Development mode (requires air for auto-reload)
dev:
	@echo "Starting development server..."
	@if command -v air > /dev/null 2>&1; then \
		cd api && air -c ../.air.toml; \
	else \
		echo "Air not installed. Install with: go install github.com/cosmtrek/air@latest"; \
		echo "Running without auto-reload..."; \
		$(MAKE) run; \
	fi

# Run tests
test:
	@echo "Running tests..."
	cd api && go test -v ./...

# Clean build artifacts
clean:
	@echo "Cleaning..."
	rm -rf bin/
	cd api && go clean

# Download dependencies
deps:
	@echo "Downloading dependencies..."
	cd api && go mod download

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