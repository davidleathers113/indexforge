"""Configuration constants for Docker testing."""

from typing import Any, Dict

# Performance thresholds
PERFORMANCE_THRESHOLDS: Dict[str, float] = {
    "startup_time": 10.0,  # seconds
    "health_check_timeout": 30.0,  # seconds
    "cpu_usage": 80.0,  # percentage
    "memory_usage": 80.0,  # percentage
    "max_processes": 20,
}

# Security settings
SECURITY_REQUIREMENTS: Dict[str, Any] = {
    "required_security_opts": ["no-new-privileges"],
    "required_capabilities_drop": ["ALL"],
    "max_user_id": 65535,
    "restricted_paths": ["/proc", "/sys"],
    "sensitive_mounts": ["/etc/passwd", "/etc/shadow"],
}

# Resource limits
RESOURCE_LIMITS: Dict[str, Any] = {
    "memory": "1g",
    "cpu_count": 1.0,
    "pids_limit": 100,
    "ulimits": {"nofile": {"soft": 1024, "hard": 2048}},
}

# Build configuration
BUILD_CONFIG: Dict[str, Any] = {
    "max_layers": 15,
    "max_image_size_mb": 1000,
    "cache_warmup_builds": 2,
}

# Test timeouts
TEST_TIMEOUTS: Dict[str, float] = {
    "build": 600.0,  # seconds
    "startup": 30.0,  # seconds
    "health_check": 30.0,  # seconds
    "performance": 300.0,  # seconds
}

# Required processes
REQUIRED_PROCESSES: Dict[str, list] = {
    "web": ["python", "gunicorn"],
    "worker": ["python", "celery"],
    "base": ["tini", "python"],
}
