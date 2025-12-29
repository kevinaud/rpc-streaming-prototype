FROM mcr.microsoft.com/devcontainers/python:3.14

# ============================================================
# Backup-Restore Pattern for Dev Container Dependencies
# ============================================================
# - Dependencies are installed at build time for caching
# - frontend/node_modules is backed up to /opt/backup (survives mount)
# - init.sh restores from backup after workspace mount
# ============================================================

# Install uv from official image (faster, always up-to-date)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Configure uv for optimal caching
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/uv-cache

# Create backup directory for node_modules
RUN mkdir -p /opt/backup

# Set working directory for dependency installation
WORKDIR /workspace

# Copy Python lockfiles first for dependency layer caching
COPY pyproject.toml uv.loc* ./

# Install Python dependencies (frozen if lock exists)
RUN if [ -s uv.lock ]; then \
      uv sync --frozen --no-install-project; \
    else \
      uv sync --no-install-project; \
    fi

# Copy full project for CI builds (dev container mounts over this)
COPY . .
