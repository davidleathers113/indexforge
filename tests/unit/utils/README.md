# Utils Tests Organization

This directory contains unit tests for the utility modules. The tests are organized into subdirectories based on functionality, with each subdirectory focusing on a specific aspect of the system.

## Directory Structure

```
utils/
├── cache/                  # Cache management tests
│   ├── test_basic_operations.py
│   ├── test_decorators.py
│   ├── test_error_handling.py
│   ├── test_integration.py
│   ├── test_key_management.py
│   └── test_retry.py
├── document/              # Document processing tests
│   ├── test_basic_operations.py
│   ├── test_batch_operations.py
│   ├── test_chunking.py
│   ├── test_config.py
│   ├── test_content_processing.py
│   ├── test_error_handling.py
│   ├── test_integration.py
│   ├── test_metadata.py
│   ├── test_performance.py
│   ├── test_processing.py
│   └── test_validation.py
├── monitoring/            # System monitoring tests
│   ├── test_config.py
│   ├── test_error_handling.py
│   ├── test_export.py
│   ├── test_metrics.py
│   ├── test_operation_tracking.py
│   ├── test_operations.py
│   ├── test_prometheus.py
│   ├── test_summary.py
│   └── test_system_metrics.py
├── pii/                   # PII detection tests
│   ├── test_document_analysis.py
│   ├── test_error_handling.py
│   ├── test_ner.py
│   ├── test_pattern_matching.py
│   └── test_redaction.py
├── summarizer/            # Text summarization tests
│   ├── test_cache_integration.py
│   ├── test_chunk_processing.py
│   ├── test_configuration.py
│   ├── test_document_processing.py
│   ├── test_error_cases.py
│   └── test_multi_chunk.py
├── text/                  # Text processing tests
│   ├── test_chunking.py
│   ├── test_error_handling.py
│   ├── test_token_management.py
│   └── test_truncation.py
└── topic/                 # Topic clustering tests
    ├── test_cache_integration.py
    ├── test_caching.py
    ├── test_clustering.py
    ├── test_config.py
    ├── test_document_processing.py
    ├── test_error_handling.py
    ├── test_keywords.py
    ├── test_similar_topics.py
    └── test_special_cases.py
```

## Test Organization

Each subdirectory follows these organizational principles:

1. **Basic Operations**: Tests for core functionality (`test_basic_operations.py`)
2. **Error Handling**: Tests for error cases and edge conditions (`test_error_handling.py`)
3. **Integration**: Tests for interaction between components (`test_integration.py`)
4. **Configuration**: Tests for configuration management (`test_config.py`)
5. **Special Cases**: Tests for specific use cases or edge scenarios

## Fixture Usage

Tests use centralized fixtures from `tests/fixtures/` directory:

- Base fixtures: `tests.fixtures.base`
- Cache fixtures: `tests.fixtures.cache`
- CLI fixtures: `tests.fixtures.cli`
- Component fixtures: `tests.fixtures.components`
- Constants: `tests.fixtures.constants`
- Document fixtures: `tests.fixtures.documents`
- Embedding fixtures: `tests.fixtures.embedding`
- Error fixtures: `tests.fixtures.errors`
- Logger fixtures: `tests.fixtures.logger`
- Pipeline core fixtures: `tests.fixtures.pipeline_core`
- Processing fixtures: `tests.fixtures.processing`
- Schema fixtures: `tests.fixtures.schema`, `tests.fixtures.schema_validator`, `tests.fixtures.schema_migrator`
- Search fixtures: `tests.fixtures.search`
- Utility fixtures: `tests.fixtures.utils`
- Vector fixtures: `tests.fixtures.vector`

Additional test utilities can be found in `tests/utils/`:

- Assertions: `tests.utils.assertions`
- Constants: `tests.utils.constants`
- Helpers: `tests.utils.helpers`
- Mocks: `tests.utils.mocks`
- Test utilities: `tests.utils.test_utils`

Local fixtures are used only when specific test configuration is needed.

## Test Categories

1. **Unit Tests**

   - Test individual functions and methods
   - Use mocked dependencies
   - Focus on specific functionality

2. **Integration Tests**

   - Test interaction between components
   - Use fixture combinations
   - Verify end-to-end flows

3. **Error Cases**

   - Verify proper error handling
   - Test edge cases and invalid inputs
   - Ensure system stability

4. **Performance Tests**
   - Test system behavior with large inputs
   - Verify resource usage
   - Check processing time

## Running Tests

Run specific test categories:

```bash
# Run all utils tests
pytest tests/unit/utils

# Run specific module tests
pytest tests/unit/utils/cache
pytest tests/unit/utils/document
pytest tests/unit/utils/topic

# Run specific test file
pytest tests/unit/utils/cache/test_basic_operations.py
```

## Adding New Tests

When adding new tests:

1. Place tests in appropriate subdirectory
2. Use centralized fixtures when possible
3. Follow existing naming conventions
4. Include proper docstrings and comments
5. Add error handling tests
6. Consider performance implications
