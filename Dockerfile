# syntax=docker/dockerfile:1

# Builder stage
FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder

# Set build-time environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.0.0 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    PYTHONPATH="/app"

# Disable pipeline downloads and configure apt
RUN echo 'Acquire::Retries "3";Acquire::http {Pipeline-Depth "0";}; Acquire::http::No-Cache=True;' > /etc/apt/apt.conf.d/99disable-pipeline

# Clean existing apt lists
RUN rm -rf /var/lib/apt/lists/*

# Install system dependencies and Poetry
RUN apt-get update --allow-releaseinfo-change --fix-missing && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgomp1 \
    git && \
    rm -rf /var/lib/apt/lists/* && \
    curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies and PyTorch (stable version)
RUN poetry install --only main --no-root && \
    pip install --no-cache-dir \
    torch==2.1.2 \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
    sentence-transformers \
    transformers

# Clean up pip cache and other temp files
RUN rm -rf /var/cache/apk/* /root/.cache/pip /var/cache/pypoetry

# Final stage
FROM --platform=$TARGETPLATFORM python:3.11-slim AS final

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME='/usr/local' \
    PYTHONPATH="/app"

WORKDIR /app

# Install runtime dependencies
RUN echo 'Acquire::Retries "3";Acquire::http {Pipeline-Depth "0";}; Acquire::http::No-Cache=True;' > /etc/apt/apt.conf.d/99disable-pipeline && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update --allow-releaseinfo-change --fix-missing && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 appuser

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/poetry /usr/local/bin/poetry
COPY src/ ./src/

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["poetry", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]