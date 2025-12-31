# Engineering Tools Platform - Cross-Platform Makefile
# Works on: Windows (Git Bash/WSL), Mac, Linux
#
# Usage:
#   make dev        - Start all services (Docker)
#   make dev-local  - Start all services (local, no Docker)
#   make stop       - Stop all services
#   make clean      - Stop and remove containers/volumes
#
# Prerequisites:
#   - Docker & Docker Compose (for `make dev`)
#   - Python 3.13+, Node 22+, uv (for `make dev-local`)

.PHONY: dev dev-local stop clean logs backend phoenix docs help

# Default target
help:
	@echo "Engineering Tools Platform"
	@echo "=========================="
	@echo ""
	@echo "Docker (recommended):"
	@echo "  make dev        Start all services with Docker Compose"
	@echo "  make stop       Stop all Docker services"
	@echo "  make clean      Stop and remove containers/volumes"
	@echo "  make logs       View Docker logs"
	@echo ""
	@echo "Local development:"
	@echo "  make dev-local  Start all services locally (no Docker)"
	@echo "  make backend    Start only backend API"
	@echo "  make phoenix    Start only Phoenix"
	@echo "  make docs       Start only MkDocs"
	@echo ""
	@echo "Ports:"
	@echo "  8000  - Backend API"
	@echo "  6006  - Phoenix"
	@echo "  8001  - MkDocs"
	@echo "  3000  - Homepage"
	@echo "  5173  - DAT Frontend"
	@echo "  5174  - SOV Frontend"
	@echo "  5175  - PPTX Frontend"

# =============================================================================
# Docker Compose (THE RIGHT WAY)
# =============================================================================

dev:
	docker compose up --build

stop:
	docker compose down

clean:
	docker compose down -v --remove-orphans

logs:
	docker compose logs -f

# =============================================================================
# Local Development (fallback if Docker unavailable)
# =============================================================================

dev-local:
	@echo "Starting services locally with honcho..."
	@if [ -f .venv/bin/honcho ]; then \
		. .venv/bin/activate && honcho start; \
	elif [ -f .venv/Scripts/honcho.exe ]; then \
		. .venv/Scripts/activate && honcho start; \
	else \
		echo "Error: honcho not found. Run 'uv sync' first."; \
		exit 1; \
	fi

backend:
	@. .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate && \
	uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload

phoenix:
	@. .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate && \
	PHOENIX_PORT=6006 python -m phoenix.server.main serve

docs:
	@. .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate && \
	mkdocs serve --dev-addr 127.0.0.1:8001

# =============================================================================
# Setup
# =============================================================================

setup:
	@echo "Setting up development environment..."
	uv sync
	cd apps/homepage/frontend && npm install
	cd apps/data_aggregator/frontend && npm install
	cd apps/sov_analyzer/frontend && npm install
	cd apps/pptx_generator/frontend && npm install
	@echo "Setup complete! Run 'make dev' to start."
