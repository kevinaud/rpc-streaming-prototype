#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PROTO_DIR="$REPO_ROOT/protos"
PYTHON_OUT="$REPO_ROOT/rpc_stream_prototype/generated"

echo "🔧 Generating Python code from proto files..."

# Clean and recreate output directory
rm -rf "$PYTHON_OUT"
mkdir -p "$PYTHON_OUT"

# Generate Python code with betterproto (using uv run to access venv)
# betterproto creates package structure based on proto package name
uv run python -m grpc_tools.protoc \
  -I "$PROTO_DIR" \
  -I "$(uv run python -c 'import grpc_tools; print(grpc_tools.__path__[0])')/_proto" \
  --python_betterproto_out="$PYTHON_OUT" \
  "$PROTO_DIR"/*.proto

# Create root __init__.py
touch "$PYTHON_OUT/__init__.py"

echo "✅ Proto generation complete: $PYTHON_OUT"
echo "📦 Generated package: rpc_stream_prototype.generated.approval.v1"
