# Schema Integration Test Documentation

## Overview

This documentation provides a comprehensive guide to the integration tests between the Core Schema System and Document Processing Schema. Each test suite is designed to validate specific aspects of the integration, ensuring robust and reliable schema handling.

## Test Categories

### Edge Cases Tests

- [Circular References](edge_cases/test_circular_references.md) - Validates detection and prevention of circular document relationships
- [Oversized Documents](edge_cases/test_oversized_documents.md) - Tests handling of documents exceeding size limits

### Error Handling Tests

- [Invalid Data Rejection](error_handling/test_invalid_data_rejection.md) - Validates rejection of invalid data during schema validation
- [Schema Mismatch](error_handling/test_schema_mismatch.md) - Tests handling of schema mismatches and incompatibilities

### Performance Tests

- [Performance and Scalability](performance/test_performance_scalability.md) - Validates system performance under various load conditions

### Property Mapping Tests

- [Custom Property Mapping](property_mapping/test_custom_property_mapping.md) - Tests mapping of custom properties between schemas

### Search Tests

- [Hybrid Search](search/test_hybrid_search.md) - Validates hybrid search capabilities (BM25 + vector similarity)
- [Query Edge Cases](search/test_query_edge_cases.md) - Tests handling of edge cases in search queries

### Validation Tests

- [Validate Relationships](validation/test_validate_relationships.md) - Ensures proper validation of document relationships
- [Validate Required Fields](validation/test_validate_required_fields.md) - Tests validation of required document fields

### Versioning Tests

- [Backward Compatibility](versioning/test_backward_compatibility.md) - Tests handling of documents with older schema versions
- [Schema Migrations](versioning/test_schema_migrations.md) - Validates schema migration processes

## Common Test Attributes

Each test suite includes:

- Clear purpose and objectives
- Detailed test cases with expected outcomes
- Risk assessment and failure impacts
- Coverage gaps identification
- Test dependencies

## Running the Tests

All tests follow pytest conventions and can be run using:

```bash
pytest tests/integration/
```

For specific test categories:

```bash
pytest tests/integration/edge_cases/
pytest tests/integration/error_handling/
pytest tests/integration/performance/
pytest tests/integration/property_mapping/
pytest tests/integration/search/
pytest tests/integration/validation/
pytest tests/integration/versioning/
```

## Test Dependencies

Common dependencies across test suites:

- SchemaValidator
- BaseProcessor
- test_document fixture
- base_schema fixture
- Various utility modules (UUID, datetime, etc.)
