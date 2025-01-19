"""Document processing integration tests package.

This package contains integration tests for the document processing system,
organized into modules for different testing scenarios:

- Sequential processing tests
- Concurrent processing tests
- Error handling tests
- Resource management tests

The tests use common utilities from base_tests.py and test data creation
from builders.py.
"""

from .base_tests import BaseProcessorTest
from .builders import DocumentBuilder, ExcelBuilder
from .factories import ProcessorTestFactory

__version__ = "1.0.0"
__all__ = ["BaseProcessorTest", "DocumentBuilder", "ExcelBuilder", "ProcessorTestFactory"]
