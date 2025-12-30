# ============================================================
# RPC Stream Prototype - Developer Makefile
# ============================================================
# This Makefile is the entry point for all common developer workflows.
# It ensures proto generation is always run before dependent tasks.
#
# Usage:
#   make help        - Show available targets
#   make generate    - Generate proto code (Python + TypeScript)
#   make server      - Start backend server
#   make frontend    - Start frontend dev server
#   make test        - Run all tests
#   make quality     - Run all quality checks
# ============================================================

.PHONY: help generate clean server frontend test test-unit test-integration quality lint format all dev

# Default target
.DEFAULT_GOAL := help

# Directories
PYTHON_GEN_DIR := rpc_stream_prototype/generated
TS_GEN_DIR := frontend/src/app/generated

# Marker file to track when protos were last generated
# This avoids regenerating if proto files haven't changed
PROTO_MARKER := .proto-generated

# Find all proto files
PROTO_FILES := $(shell find protos -name '*.proto' 2>/dev/null)

# ============================================================
# Help
# ============================================================
help:
	@echo "RPC Stream Prototype - Developer Commands"
	@echo ""
	@echo "Proto Generation:"
	@echo "  make generate     - Generate proto code (Python + TypeScript)"
	@echo "  make clean        - Remove all generated code"
	@echo ""
	@echo "Development Servers:"
	@echo "  make server       - Start backend gRPC server"
	@echo "  make frontend     - Start frontend Angular dev server"
	@echo "  make dev          - Start both backend and frontend (requires tmux)"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-int     - Run integration tests only"
	@echo ""
	@echo "Quality:"
	@echo "  make quality      - Run all quality checks (lint, format, types)"
	@echo "  make lint         - Run linters only"
	@echo "  make format       - Auto-format all code"
	@echo ""
	@echo "CLI:"
	@echo "  make cli          - Run the proposer CLI"

# ============================================================
# Proto Generation
# ============================================================

# Generate protos only if source files changed
$(PROTO_MARKER): $(PROTO_FILES) buf.yaml buf.gen.yaml
	@echo "🔧 Generating code from proto files..."
	@rm -rf "$(PYTHON_GEN_DIR)" "$(TS_GEN_DIR)"
	@buf generate
	@touch "$(PYTHON_GEN_DIR)/__init__.py"
	@echo "🎨 Formatting Python generated code..."
	@uv run ruff check --fix "$(PYTHON_GEN_DIR)" 2>/dev/null || true
	@uv run ruff format "$(PYTHON_GEN_DIR)"
	@echo "🎨 Formatting TypeScript generated code..."
	@cd frontend && npx prettier --write "src/app/generated/**/*.ts" 2>/dev/null || true
	@touch $(PROTO_MARKER)
	@echo "✅ Proto generation complete!"

generate: $(PROTO_MARKER)

# Force regeneration
regenerate:
	@rm -f $(PROTO_MARKER)
	@$(MAKE) generate

clean:
	@echo "🧹 Cleaning generated code..."
	@rm -rf "$(PYTHON_GEN_DIR)" "$(TS_GEN_DIR)" $(PROTO_MARKER)
	@echo "✅ Clean complete!"

# ============================================================
# Development Servers
# ============================================================

server: generate
	@echo "🚀 Starting backend gRPC server..."
	uv run python -m rpc_stream_prototype.backend.main

frontend: generate
	@echo "🚀 Starting frontend Angular dev server..."
	cd frontend && npm start

# Start both servers (requires tmux or run in separate terminals)
dev:
	@echo "Starting development environment..."
	@echo "Run 'make server' and 'make frontend' in separate terminals"
	@echo "Or use: tmux new-session 'make server' \\; split-window 'make frontend'"

# ============================================================
# CLI
# ============================================================

cli: generate
	@echo "🖥️  Starting Proposer CLI..."
	uv run python -m rpc_stream_prototype.cli.main

# ============================================================
# Testing
# ============================================================

test: generate
	@echo "🧪 Running all tests..."
	uv run pytest

test-unit: generate
	@echo "🧪 Running unit tests..."
	uv run pytest tests/unit -v

test-int: generate
	@echo "🧪 Running integration tests..."
	uv run pytest tests/integration -v

# ============================================================
# Quality Checks
# ============================================================

quality: generate
	@echo "🔍 Running quality checks..."
	./scripts/check_quality.sh

lint: generate
	@echo "🔍 Running linters..."
	@echo "--- Proto ---"
	buf lint
	@echo "--- Python ---"
	uv run ruff check .
	uv run pyright
	@echo "--- TypeScript ---"
	cd frontend && npm run lint

format:
	@echo "🎨 Formatting all code..."
	@echo "--- Proto ---"
	buf format -w
	@echo "--- Python ---"
	uv run ruff check --fix . || true
	uv run ruff format .
	@echo "--- TypeScript ---"
	cd frontend && npx prettier --write "src/**/*.{ts,html,scss}"
	@echo "✅ Formatting complete!"
