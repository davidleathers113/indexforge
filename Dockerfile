# syntax=docker/dockerfile:1.4

# Build arguments for better flexibility and caching
ARG PYTHON_VERSION=3.11
ARG POETRY_VERSION=2.0.0
ARG BUILD_ENV=production
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG SERVICE_VERSION=1.0.0
ARG MAX_REQUEST_SIZE_MB=2
ARG MAX_CONTENT_LENGTH=1048576

# Poetry installation stage
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-slim AS poetry
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Builder stage
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-slim AS builder
COPY --from=poetry /opt/poetry /opt/poetry
COPY --from=poetry /usr/local/bin/poetry /usr/local/bin/poetry

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH="/app"

WORKDIR /app

# Install build dependencies with improved caching
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgomp1 \
    git && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies with improved caching
COPY pyproject.toml poetry.lock ./
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    --mount=type=cache,target=/root/.cache/poetry,sharing=locked \
    poetry install --only main,storage,parsing,monitoring --no-root

# Security scanning stage
FROM aquasec/trivy:latest AS security-scan
COPY --from=builder /app /app
RUN trivy filesystem --no-progress --ignore-unfixed --severity HIGH,CRITICAL /app

# Final stage
FROM --platform=$TARGETPLATFORM python:${PYTHON_VERSION}-slim AS final

LABEL org.opencontainers.image.vendor="IndexForge" \
    org.opencontainers.image.title="IndexForge API" \
    org.opencontainers.image.description="Universal file indexing and processing system" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.version=${SERVICE_VERSION} \
    org.opencontainers.image.revision=${GIT_COMMIT}

# Application configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    PORT=8000 \
    API_PORT=8000 \
    ENVIRONMENT=production \
    MAX_REQUEST_SIZE_MB=${MAX_REQUEST_SIZE_MB} \
    MAX_CONTENT_LENGTH=${MAX_CONTENT_LENGTH} \
    ERROR_LOG_LEVEL=notice \
    ERROR_TEMPLATES_PATH=/usr/local/kong/templates

# Service timeouts
ENV APP_CONNECT_TIMEOUT=3000 \
    APP_WRITE_TIMEOUT=5000 \
    APP_READ_TIMEOUT=60000 \
    ML_CONNECT_TIMEOUT=5000 \
    ML_WRITE_TIMEOUT=10000 \
    ML_READ_TIMEOUT=120000

# Health check configuration
ENV HEALTH_CHECK_ACTIVE_ENABLED=true \
    HEALTH_CHECK_PASSIVE_ENABLED=true \
    HEALTH_CHECK_THRESHOLD=0.5 \
    HEALTH_CHECK_LOG_PATH=/usr/local/kong/logs/healthcheck.log \
    HEALTH_CHECK_LOG_LEVEL=notice \
    HEALTHY_SUCCESS_COUNT=2 \
    UNHEALTHY_FAILURE_COUNT=3

# Memory and performance settings
ENV MALLOC_ARENA_MAX=2 \
    MAX_UPSTREAM_LATENCY=5000 \
    MAX_TOTAL_LATENCY=10000 \
    LATENCY_WARNING_THRESHOLD=2000

WORKDIR /app

# Install runtime dependencies with improved caching
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -r appgroup && \
    useradd -r -g appgroup appuser && \
    mkdir -p /app/data /usr/local/kong/logs /usr/local/kong/templates && \
    chown -R appuser:appgroup /app /usr/local/kong/logs /usr/local/kong/templates

# Copy Python packages and application code
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --chown=appuser:appgroup src ./src

# Set resource constraints and security options
USER appuser:appgroup
EXPOSE $PORT

# Add resource limits
STOPSIGNAL SIGTERM

# Enhanced health check with timeout
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Use exec form with explicit Python path
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]