#!/bin/bash
# ============================================================
# Presubmit Checks
# ============================================================
# Runs the full suite of CI checks:
# 1. Quality checks (linting, formatting, proto generation)
# 2. Backend tests (unit and integration)
# 3. Frontend tests
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🚀 Starting Presubmit Checks..."

# Run Quality Checks
echo ""
echo "📋 Running Quality Checks..."
./scripts/check_quality.sh

# Run Unit and Integration Tests
echo ""
echo "🧪 Running Backend Tests..."
# (sequential - async tests need single event loop)
uv run pytest tests/unit tests/integration -v

# Run Frontend Tests
echo ""
echo "🧪 Running Frontend Tests..."
cd frontend
CI=true npm run ng -- test --watch=false

echo ""
echo "✅ All presubmit checks passed!"
