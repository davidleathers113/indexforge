"""Error monitoring and management.

This package provides functionality for monitoring and managing system errors:
- Error logging and tracking
- Error lifecycle management
- Error metrics collection
"""

from .lifecycle.manager import ErrorLoggingManager
from .models.log_entry import LogEntry, LogLevel

__all__ = [
    # Core components
    "ErrorLoggingManager",
    # Error models
    "LogEntry",
    "LogLevel",
]
