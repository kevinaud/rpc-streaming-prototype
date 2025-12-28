#!/bin/bash
set -e

echo "Running Ruff Check..."
uv run ruff check .

echo "Running Ruff Format Check..."
uv run ruff format --check .

echo "Running Pyright..."
uv run pyright
