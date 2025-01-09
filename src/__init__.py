"""Source package initialization.

This is the root package of the document processing and indexing system. It provides:

1. Version Information:
   - Current version: 0.1.0
   - Version tracking for package releases
   - Compatibility information

2. Package Structure:
   - Models subpackage for data structures
   - Utilities for common operations
   - Pipeline components for document processing
   - Connectors for external services

3. Package Exports:
   - Models module for public access
   - Core functionality through submodules
   - Type definitions and interfaces

Usage:
    ```python
    from src import models
    from src import __version__

    print(f"Package version: {__version__}")
    ```

Note:
    - Maintains backward compatibility
    - Provides stable public interfaces
    - Follows semantic versioning
"""

__version__ = "0.1.0"

from . import models

__all__ = ["models"]
