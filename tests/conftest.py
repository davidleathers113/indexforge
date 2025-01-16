"""Global test configuration with minimal dependencies."""

import tracemalloc


def pytest_configure(config):
    """Configure pytest with enhanced exception handling."""
    tracemalloc.start()


def pytest_unconfigure(config):
    """Cleanup pytest configuration."""
    tracemalloc.stop()
