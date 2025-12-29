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
# Proto Generation Check
# ============================================================
echo ""
echo "----------------------------------------"
echo "  Proto Generation Check"
echo "----------------------------------------"

echo "Checking if generated protos are up to date..."
./scripts/gen_protos.sh > /dev/null

# Check for changes in the generated directory
if [[ -n $(git status --porcelain rpc_stream_prototype/generated) ]]; then
  echo "❌ Generated protos are not up to date!"
  echo "   Please run './scripts/gen_protos.sh' and commit the changes."
  echo "   Diff:"
  git diff rpc_stream_prototype/generated
  exit 1
fi

echo "✅ Protos are up to date!"

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
