#!/bin/bash
# ============================================================
# Dev Container Initialization Script
# ============================================================
# Restores dependencies from backup after workspace mount
# and syncs to catch any drift from lockfile changes
# ============================================================

set -e

echo "🚀 Initializing dev container..."

# ------------------------------------------------------------
# Node.js Dependencies: Restore from backup
# ------------------------------------------------------------
if [ -d "/opt/backup/node_modules" ]; then
    if [ ! -d "node_modules" ] || [ -z "$(ls -A node_modules 2>/dev/null)" ]; then
        echo "📦 Restoring node_modules from backup..."
        cp -r /opt/backup/node_modules ./node_modules
    fi
fi

# Sync npm dependencies to catch any drift
if [ -f "package.json" ]; then
    echo "📦 Syncing npm dependencies..."
    npm install
fi

# ------------------------------------------------------------
# Python Dependencies: Sync with uv
# ------------------------------------------------------------
echo "🐍 Syncing Python dependencies..."
uv sync

# ------------------------------------------------------------
# GitHub CLI Auto-Login (from legacy post-start.sh)
# ------------------------------------------------------------
if [ -s /tmp/.gh_token_file ]; then
    echo "🔑 Auto-logging into GitHub CLI..."
    cat /tmp/.gh_token_file | gh auth login --with-token
else
    echo "⚠️  No GitHub token found. Skipping auto-login."
fi

echo "✅ Dev container initialization complete!"
