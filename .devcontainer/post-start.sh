#!/bin/bash
# ============================================================
# Dev Container Post-Start Script
# ============================================================
# Runs every time the container starts (not just on create)
# ============================================================

# ------------------------------------------------------------
# GitHub CLI Auto-Login
# ------------------------------------------------------------
# The token file is bind-mounted from the host at container start.
# This must run in postStartCommand (not postCreateCommand)
# because the mount isn't available during image build/create.
# ------------------------------------------------------------
if [ -s /tmp/.gh_token_file ]; then
    echo "🔑 Auto-logging into GitHub CLI..."
    cat /tmp/.gh_token_file | gh auth login --with-token
    echo "✅ GitHub CLI authenticated"
else
    echo "⚠️  No GitHub token found at /tmp/.gh_token_file"
    echo "   To enable auto-login, create ~/.gh_token_file on your host"
    echo "   with a GitHub personal access token."
fi
