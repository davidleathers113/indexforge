"""Integration tests for batch processing service interactions.

This package contains integration tests that verify the interaction between
the batch processor and various services (Redis, Weaviate, document storage).
Tests cover:
- Basic service operations
- Concurrent processing
- Error handling
- Resource management
"""

from .test_batch_service_integration import TestBatchServiceIntegration

__all__ = ["TestBatchServiceIntegration"]
