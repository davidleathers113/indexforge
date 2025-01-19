"""Integration tests for API functionality.

This package contains integration tests that verify the API's functionality,
including document management, search operations, error handling, and
performance characteristics. Tests are organized into modules:

- document/: Document management endpoint tests
- search/: Search operation tests
- test_error_handling.py: Error handling and validation tests
- test_performance.py: Performance and resource management tests
"""

from .document.test_document_management import (
    test_batch_upload_documents,
    test_delete_document,
    test_document_stats,
    test_download_document,
    test_get_document,
    test_list_documents,
    test_upload_document,
)
from .search.test_search_operations import (
    test_empty_search_results,
    test_filtered_search,
    test_search_pagination,
    test_search_ranking,
    test_search_with_date_filter,
    test_semantic_search,
)
from .test_error_handling import (
    test_concurrent_delete,
    test_file_size_limit,
    test_invalid_batch_upload,
    test_invalid_document_id,
    test_invalid_file_type,
    test_invalid_filter_parameters,
    test_invalid_search_query,
    test_malformed_request,
)
from .test_performance import (
    test_concurrent_requests,
    test_endpoint_stability,
    test_memory_usage,
    test_resource_limits,
    test_response_times,
)

__all__ = [
    # Document management tests
    "test_upload_document",
    "test_batch_upload_documents",
    "test_list_documents",
    "test_get_document",
    "test_delete_document",
    "test_document_stats",
    "test_download_document",
    # Search operation tests
    "test_semantic_search",
    "test_filtered_search",
    "test_search_pagination",
    "test_search_ranking",
    "test_search_with_date_filter",
    "test_empty_search_results",
    # Error handling tests
    "test_invalid_file_type",
    "test_file_size_limit",
    "test_invalid_document_id",
    "test_invalid_search_query",
    "test_invalid_filter_parameters",
    "test_malformed_request",
    "test_concurrent_delete",
    "test_invalid_batch_upload",
    # Performance tests
    "test_response_times",
    "test_concurrent_requests",
    "test_memory_usage",
    "test_resource_limits",
    "test_endpoint_stability",
]
