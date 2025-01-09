# Testing Infrastructure

This document outlines the testing infrastructure and conventions used in this project.

## Directory Structure

```
tests/
├── data/                  # Test data files
│   └── sample_documents.json  # Sample documents for testing
├── fixtures/              # Reusable test fixtures
│   ├── components.py      # Mock components (cache, processors, etc.)
│   ├── documents.py       # Document fixtures and data loading
│   ├── errors.py         # Error simulation fixtures
│   └── pipeline.py       # Pipeline and CLI-related fixtures
├── unit/                 # Unit tests
│   ├── indexing/         # Vector indexing tests
│   ├── pipeline/         # Pipeline-specific tests
│   └── utils/           # Utility function tests
└── conftest.py          # Global fixture configuration
```

## Test Fixtures

### Component Mocks (`fixtures/components.py`)

- `mock_cache_manager`: Mock for caching functionality
  - Simulates cache hits/misses
  - Tracks get/set operations
  - Handles document and batch caching
- `mock_doc_processor`: Mock for document processing operations
  - Handles document validation
  - Computes document hashes for deduplication
  - Prepares documents for storage
- `mock_weaviate_client`: Mock for Weaviate vector database operations
  - Simulates batch operations with context management
  - Handles test mode document IDs
  - Tracks batch processing calls

### Document Fixtures (`fixtures/documents.py`)

- `sample_document`: Basic document for testing
- `sample_documents`: List of sample documents
- `document_with_relationships`: Document with parent/reference relationships
- `large_document`: Document for testing chunking/batching

### Test Mode Support

The testing infrastructure includes a test mode that:

- Uses predictable document IDs (e.g., "test-id-1", "test-id-2")
- Simulates batch operations without actual database calls
- Handles test-specific UUID validation
- Maintains batch context for proper cleanup

### Mock Behaviors

Components are mocked to provide consistent, predictable behavior:

- Cache operations return predefined values
- Document processing maintains document structure
- API calls return mock responses
- Database operations simulate success scenarios
- Batch operations track context management
- UUID handling supports both test and production modes

## Usage

### Basic Test Structure

```python
def test_some_functionality(mock_cache_manager, sample_document):
    # Test setup with test mode
    component = Component(test_mode=True)

    # Test execution
    result = component.process(sample_document)

    # Assertions
    assert result.status == "success"
    assert mock_cache_manager.get.called
```

### Test Mode Example

```python
def test_document_operations(vector_index, sample_document):
    # Test mode automatically uses test IDs
    doc_ids = vector_index.add_documents([sample_document])
    assert doc_ids[0] == "test-id-1"

    # Batch operations are tracked
    assert mock_weaviate_client.batch.__enter__.called
```

### Fixture Scopes

- Function scope (default): Fresh instance for each test
- Session scope: Shared instance across all tests
- Module scope: Shared instance within a module

## Best Practices

1. Use appropriate fixture scopes to optimize test performance
2. Keep test data in JSON files, not hardcoded in tests
3. Use the mock_cache_manager for all caching operations
4. Simulate both success and error scenarios
5. Test edge cases (empty documents, large batches, etc.)
6. Use descriptive test names that indicate what's being tested
7. Enable test mode for predictable document IDs
8. Verify batch context management
9. Handle both test and production UUIDs
10. Clean up resources properly

## Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/unit/indexing/test_document_operations.py

# Run with verbose output
python -m pytest -v

# Run tests matching a pattern
python -m pytest -k "document_operations"
```

## Adding New Tests

1. Place tests in appropriate directory under `tests/unit/`
2. Use existing fixtures when possible
3. Create new fixtures in relevant fixture module if needed
4. Add test data to `sample_documents.json` if required
5. Follow existing naming and organization patterns
6. Enable test mode when predictable IDs are needed
7. Verify batch operations and context management

## Debugging Tests

- Use `-v` flag for verbose output
- Use `-s` flag to see print statements
- Use `pytest.set_trace()` for debugging
- Check fixture scopes if tests interfere with each other
- Monitor batch context management
- Verify test mode behavior

## Test Configuration

### Pytest Markers

The following markers are available for test organization and control:

- `@pytest.mark.slow`: Mark tests that take longer to run
- `@pytest.mark.issue(number)`: Reference specific issue numbers
- `@pytest.mark.filterwarnings`: Control warning behavior
- `@pytest.mark.batch`: Mark tests that use batch operations

### Command Line Options

Additional pytest command line options:

```bash
# Run slow tests
pytest --slow

# Run tests for specific issues
pytest --issue=123,456

# Skip specific test categories
pytest --skip-slow
pytest --skip-network
```

## Test Data Management

- Test data is stored in JSON format in `tests/data/`
- Fixtures handle data loading and transformation
- Large documents are generated dynamically
- Relationship data is structured for graph testing
- Test mode uses predictable document IDs

## Safe Teardown Practices

- Mock objects implement proper cleanup
- Resource cleanup happens even on test failures
- Temporary files are removed after tests
- Database connections are properly closed
- Batch contexts are properly managed
- Cache is cleared between test runs

## Test Isolation

- Tests use separate fixtures for independence
- Mock objects prevent external dependencies
- Cache is cleared between test modules
- Environment variables are reset after tests
- Test mode prevents database pollution
- Batch operations are properly isolated
