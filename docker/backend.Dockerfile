FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (without project itself - installed later with source)
RUN uv sync --frozen --no-install-project

# Copy source (for initial build; volume mount overrides in dev)
COPY rpc_stream_prototype/ ./rpc_stream_prototype/

# Install the project itself now that source is available
RUN uv sync --frozen
