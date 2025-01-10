FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry==2.0.0

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only ml --no-root \
    && poetry install --only main --no-root

# Copy application code
COPY src/ml ./src/ml

# Create non-root user
RUN useradd -m -u 1000 mluser \
    && chown -R mluser:mluser /app

USER mluser

# Expose port for ML service
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Command to run the ML service
CMD ["uvicorn", "src.ml.service:app", "--host", "0.0.0.0", "--port", "8001"]