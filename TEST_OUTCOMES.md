# Schema Integration Test Outcomes

## Overview

This document provides a high-level summary of all integration test outcomes between the Core Schema System and Document Processing Schema. For detailed documentation, please refer to the [Integration Test Documentation](tests/integration/docs/README.md).

## Test Categories

### Edge Cases

- [Circular References](tests/integration/docs/edge_cases/test_circular_references.md) - Detection and handling of circular document relationships
- [Oversized Documents](tests/integration/docs/edge_cases/test_oversized_documents.md) - Handling of documents exceeding size limits

### Error Handling

- [Invalid Data Rejection](tests/integration/docs/error_handling/test_invalid_data_rejection.md) - Validation and rejection of invalid data
- [Schema Mismatch](tests/integration/docs/error_handling/test_schema_mismatch.md) - Handling of schema incompatibilities

### Performance

- [Performance and Scalability](tests/integration/docs/performance/test_performance_scalability.md) - System performance under various load conditions

### Property Mapping

- [Custom Property Mapping](tests/integration/docs/property_mapping/test_custom_property_mapping.md) - Custom property mapping between schemas

### Search

- [Hybrid Search](tests/integration/docs/search/test_hybrid_search.md) - Combined BM25 and vector similarity search
- [Query Edge Cases](tests/integration/docs/search/test_query_edge_cases.md) - Edge case handling in search queries

### Validation

- [Validate Relationships](tests/integration/docs/validation/test_validate_relationships.md) - Document relationship validation
- [Validate Required Fields](tests/integration/docs/validation/test_validate_required_fields.md) - Required field validation

### Versioning

- [Backward Compatibility](tests/integration/docs/versioning/test_backward_compatibility.md) - Compatibility with older schema versions
- [Schema Migrations](tests/integration/docs/versioning/test_schema_migrations.md) - Schema migration processes

## Running Tests

For instructions on running tests and test configuration, refer to the [Integration Test Documentation](tests/integration/docs/README.md#running-the-tests).
