"""Logger performance tests.

This module has been refactored into smaller, more focused modules under the logger/ directory.
It is maintained for backward compatibility.
"""

from .logger.test_basic_logging import (
    test_concurrent_logging,
    test_large_messages,
    test_malformed_json,
    test_missing_fields,
)
from .logger.test_performance import test_validation_performance
from .logger.test_streaming_validation import (
    test_streaming_validation_large_file,
    test_streaming_validation_with_size_limits,
    test_streaming_with_data,
)
