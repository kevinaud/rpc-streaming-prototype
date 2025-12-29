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

# Create a temporary directory for generation verification
# We create it inside the project root so that ruff can find pyproject.toml
TEMP_GEN_DIR="rpc_stream_prototype/generated_check_tmp"
mkdir -p "$TEMP_GEN_DIR"

# Ensure cleanup on exit
cleanup() {
  rm -rf "$TEMP_GEN_DIR"
}
trap cleanup EXIT

# Generate protos to the temp directory
./scripts/gen_protos.sh "$TEMP_GEN_DIR" > /dev/null

# Compare the current generated directory with the fresh generation
# We use diff -r to compare directories recursively, excluding __pycache__
if ! diff -r --exclude=__pycache__ "rpc_stream_prototype/generated" "$TEMP_GEN_DIR"; then
  echo "❌ Generated protos are not up to date!"
  echo "   The generated code in 'rpc_stream_prototype/generated' does not match what is produced by the current protos."
  echo "   Please run './scripts/gen_protos.sh' to update them."
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
