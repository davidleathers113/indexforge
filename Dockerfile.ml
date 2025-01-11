# syntax=docker/dockerfile:1.4
ARG PYTHON_VERSION=3.11
ARG POETRY_VERSION=2.0.0

# Build stage
FROM python:${PYTHON_VERSION}-slim AS builder

# Build arguments
ARG BUILD_ENV=production
ARG POETRY_VERSION
ARG TARGETARCH

# Add metadata labels
LABEL org.opencontainers.image.title="IndexForge ML Service"
LABEL org.opencontainers.image.description="Machine Learning service for IndexForge"
LABEL org.opencontainers.image.version=${BUILD_ENV}

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry using cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install poetry==${POETRY_VERSION}

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry config virtualenvs.create false && \
    poetry install --only ml --no-root && \
    poetry install --only main --no-root

# Security scanning stage
FROM aquasec/trivy:latest AS security
WORKDIR /app
COPY --from=builder /app /app
RUN trivy filesystem --no-progress --ignore-unfixed --severity HIGH,CRITICAL /app

# Final stage
FROM python:${PYTHON_VERSION}-slim AS final

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ml ./src/ml

# Create non-root user
RUN useradd -m -u 1000 mluser \
    && chown -R mluser:mluser /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    MALLOC_ARENA_MAX=2

USER mluser

# Expose port for ML service
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Stop signal
STOPSIGNAL SIGTERM

# Command to run the ML service
CMD ["python", "-m", "uvicorn", "src.ml.service:app", "--host", "0.0.0.0", "--port", "8001"]