#!/bin/bash
# ============================================================
# Dev Container Initialization Script
# ============================================================
# Syncs dependencies after workspace mount.
# 
# This runs as postCreateCommand (once after container create).
# See post-start.sh for things that run every container start.
# ============================================================

set -e

echo "🚀 Initializing dev container..."

# ------------------------------------------------------------
# Fix uv-cache permissions (for CI runner compatibility)
# ------------------------------------------------------------
if [ -d "/opt/uv-cache" ]; then
    if [ ! -w "/opt/uv-cache" ]; then
        echo "🔧 Fixing uv-cache permissions..."
        sudo chown -R "$(id -u):$(id -g)" /opt/uv-cache 2>/dev/null || true
    fi
fi

# ------------------------------------------------------------
# Python Dependencies: Sync with uv
# ------------------------------------------------------------
echo "🐍 Syncing Python dependencies..."
uv sync

# ------------------------------------------------------------
# Frontend Node.js Dependencies
# ------------------------------------------------------------
if [ -f "frontend/package.json" ]; then
    echo "📦 Installing frontend npm dependencies..."
    (cd frontend && npm install)
fi

# ------------------------------------------------------------
# Install Angular CLI globally
# ------------------------------------------------------------
if ! command -v ng &> /dev/null; then
    echo "📦 Installing Angular CLI globally..."
    npm install -g @angular/cli
fi

echo "✅ Dev container initialization complete!"
