#!/bin/bash
# ============================================================
# Unified Quality Check Script
# ============================================================
# Runs code quality checks for both Python backend and Angular frontend.
# Exits immediately if any check fails.
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "========================================"
echo "  Code Quality Checks"
echo "========================================"

# ============================================================
# Python Backend Checks
# ============================================================
echo ""
echo "----------------------------------------"
echo "  Python Backend"
echo "----------------------------------------"

echo "Running Pyright (type check)..."
uv run pyright

echo "Running Ruff (lint)..."
uv run ruff check .

echo "Running Ruff (format check)..."
uv run ruff format --check .

echo "✅ Python checks passed!"

# ============================================================
# Angular Frontend Checks
# ============================================================
echo ""
echo "----------------------------------------"
echo "  Angular Frontend"
echo "----------------------------------------"

cd "$PROJECT_ROOT/frontend"

echo "Running Angular build (AOT strict template verification)..."
npm run ng -- build --configuration production --no-progress

echo "Running ESLint..."
npm run ng -- lint

echo "Running Prettier (format check)..."
npx prettier --check "src/**/*.{ts,html,scss}"

echo "✅ Angular checks passed!"

# ============================================================
# Summary
# ============================================================
echo ""
echo "========================================"
echo "  ✅ All quality checks passed!"
echo "========================================"
