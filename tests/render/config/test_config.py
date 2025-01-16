"""Configuration constants for Render testing."""

from typing import Any


# Performance thresholds
PERFORMANCE_THRESHOLDS: dict[str, float] = {
    "startup_time": 300.0,  # seconds
    "build_time": 600.0,  # seconds
    "cpu_usage": 80.0,  # percentage
    "memory_usage": 80.0,  # percentage
}

# Required environment variables
REQUIRED_ENV_VARS: dict[str, list] = {
    "base": ["PYTHON_VERSION", "POETRY_VERSION", "ENVIRONMENT"],
    "web": ["PORT", "HOST", "MAX_WORKERS"],
    "worker": ["CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"],
}

# Build steps
REQUIRED_BUILD_STEPS: list = [
    "Installing Poetry",
    "Installing dependencies",
    "Running build command",
    "Collecting static files",
    "Running tests",
    "Building assets",
]

# Security settings
SECURITY_REQUIREMENTS: dict[str, Any] = {
    "cors_settings": {
        "allowed_origins": ["https://*"],
        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    },
    "ssl_settings": {
        "min_tls_version": "1.2",
        "hsts_enabled": True,
    },
    "required_headers": {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    },
}

# Resource limits
SERVICE_LIMITS: dict[str, Any] = {
    "web": {
        "memory": 512,  # MB
        "cpu": 1.0,
        "max_requests": 1000,
    },
    "worker": {
        "memory": 1024,  # MB
        "cpu": 2.0,
        "max_tasks": 100,
    },
}

# Test timeouts
TEST_TIMEOUTS: dict[str, float] = {
    "deployment": 600.0,  # seconds
    "health_check": 60.0,  # seconds
    "build": 900.0,  # seconds
    "performance": 300.0,  # seconds
}

# Cache settings
CACHE_CONFIG: dict[str, Any] = {
    "build_cache_enabled": True,
    "cache_warmup_builds": 2,
    "expected_cache_improvement": 0.3,  # 30% faster
}
