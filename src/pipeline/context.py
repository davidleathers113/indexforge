"""Pipeline context management.

This module provides context management utilities for pipeline resources,
ensuring proper initialization, cleanup, and error handling during pipeline
execution.

Features:
1. Resource Management:
   - Automatic resource initialization
   - Guaranteed cleanup on completion
   - Error handling during cleanup
   - Resource state tracking

2. Error Handling:
   - Exception conversion and wrapping
   - Detailed error logging
   - Stack trace preservation
   - Error cause tracking

3. Logging:
   - Detailed operation logging
   - Error tracking
   - Resource state changes
   - Performance monitoring

Usage:
    ```python
    from pipeline.context import managed_pipeline
    from pipeline.core import Pipeline

    pipeline = Pipeline(export_dir="/path/to/export")

    with managed_pipeline(pipeline) as p:
        p.process_documents()
    ```

Note:
    - Ensures cleanup even after errors
    - Preserves original error context
    - Provides detailed logging
    - Handles nested resources
"""

from collections.abc import Generator
from contextlib import contextmanager
import logging
import traceback

from .errors import ResourceError


@contextmanager
def managed_pipeline(pipeline) -> Generator:
    """Context manager for pipeline resources.

    Ensures proper cleanup of resources even if errors occur during pipeline
    execution. Provides comprehensive error handling and logging.

    Args:
        pipeline: Pipeline instance to manage

    Yields:
        Pipeline instance with initialized resources

    Raises:
        ResourceError: If error occurs during pipeline operations, wraps original error
    """
    logger = logging.getLogger(__name__)
    logger.info("Initializing pipeline resources")

    try:
        logger.debug("Yielding pipeline instance")
        yield pipeline
    except Exception as e:
        # Log detailed error information
        logger.error(
            "Pipeline operation failed: %s: %s", e.__class__.__name__, str(e), exc_info=True
        )
        logger.debug("Stack trace:\n%s", "".join(traceback.format_tb(e.__traceback__)))

        # Convert to ResourceError while preserving original cause
        raise ResourceError("Pipeline operation failed") from e
    finally:
        logger.info("Cleaning up pipeline resources")
        try:
            pipeline.cleanup()
            logger.info("Pipeline resources cleaned up successfully")
        except Exception as e:
            # Log detailed cleanup error but don't raise to ensure original error is propagated
            logger.error(
                "Failed to cleanup pipeline resources: %s: %s",
                e.__class__.__name__,
                str(e),
                exc_info=True,
            )
            logger.debug("Cleanup stack trace:\n%s", "".join(traceback.format_tb(e.__traceback__)))
