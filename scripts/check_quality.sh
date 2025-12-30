#!/bin/bash
# ============================================================
# Unified Quality Check Script
# ============================================================
# Runs code quality checks for both Python backend and Angular frontend.
# Exits immediately if any check fails.
#
# NOTE: This script assumes protos have already been generated.
#       Use `make quality` to ensure generation runs first.
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "========================================"
echo "  Code Quality Checks"
echo "========================================"

# ============================================================
# Proto Linting & Formatting
# ============================================================
echo ""
echo "----------------------------------------"
echo "  Proto Linting & Formatting"
echo "----------------------------------------"

# Check if buf is installed
if ! command -v buf &> /dev/null; then
    echo "⚠️  'buf' is not installed. Skipping proto checks."
    echo "   Install via npm: npm install -g @bufbuild/buf"
else
    echo "Running Buf Lint..."
    # Lints the protos directory based on buf.yaml rules
    buf lint

    echo "Running Buf Format (Check)..."
    # --diff: Shows the difference
    # --exit-code: Fails the script if changes are needed
    buf format --diff --exit-code
    
    echo "✅ Proto static analysis passed!"
fi

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
CI=true npm run ng -- build --configuration production --no-progress

echo "Running ESLint..."
CI=true npm run ng -- lint

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
