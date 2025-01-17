"""Settings models for the application.

This module defines configuration settings for various components
of the application, including storage, metrics, and general options.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """Application settings."""

    # Storage settings
    storage_path: Path
    max_metrics_history: int = 1000  # Maximum number of metrics entries to keep per operation
    metrics_enabled: bool = True  # Whether to collect metrics

    # Performance settings
    batch_size: int = 100  # Default batch size for operations
    max_concurrent_operations: int = 4  # Maximum number of concurrent operations

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    def __post_init__(self) -> None:
        """Validate and process settings after initialization."""
        if isinstance(self.storage_path, str):
            self.storage_path = Path(self.storage_path)
        if isinstance(self.log_file, str):
            self.log_file = Path(self.log_file)

        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
