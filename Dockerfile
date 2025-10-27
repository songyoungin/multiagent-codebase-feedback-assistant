# Use Python 3.13 slim image
FROM python:3.13-slim

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation for better startup performance
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./
COPY README.md ./

# Install dependencies only (separate layer for caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy source code
COPY agents/ ./agents/
COPY common/ ./common/
COPY tools/ ./tools/
COPY typings/ ./typings/

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Set Python path
ENV PYTHONPATH=/app

# Expose ports for all agents (including orchestrator on 8306)
EXPOSE 8301 8302 8303 8304 8305 8306

# Default command (will be overridden by docker-compose)
CMD ["uv", "run", "python", "-m", "agents.project_scanner.project_scanner_server"]
