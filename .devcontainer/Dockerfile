FROM mcr.microsoft.com/devcontainers/python:3.14

# Install uv for dependency management during build
RUN pip install uv

# Copy dependency files for caching
# Using uv.loc* pattern so COPY doesn't fail if uv.lock doesn't exist
COPY pyproject.toml uv.loc* ./

# Install dependencies only (not the local project, since source isn't in container yet)
# The local project will be installed when the workspace is mounted
# Use --frozen only if lock file exists and is not empty, otherwise generate it
RUN if [ -s uv.lock ]; then \
      uv sync --frozen --no-install-project; \
    else \
      uv sync --no-install-project; \
    fi

