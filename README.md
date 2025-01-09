# IndexForge

A powerful universal file indexing and processing system, with specialized support for Notion workspace exports. This project processes Notion workspace exports, generates embeddings for the content, and creates a searchable vector database for semantic search and retrieval.

## Features

- Processes Notion workspace exports (CSV format)
- Generates embeddings using OpenAI's text-embedding-ada-002 model
- Creates a vector database using Weaviate
- Supports semantic search and filtered queries
- Handles document relationships and metadata

## Setup

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

2. Set up environment variables in a `.env` file:

```
OPENAI_API_KEY=your_openai_api_key
WEAVIATE_URL=your_weaviate_instance_url  # Default: http://localhost:8080
```

3. Place your Notion workspace export in the `notion-workspace-export` directory.

## Usage

Run the main script to process your Notion export:

```bash
python src/main.py
```

This will:

1. Load and normalize the Notion data
2. Generate embeddings for all documents
3. Index the documents in Weaviate

## Project Structure

```
src/
├── connectors/          # Data source connectors
│   └── notion_connector.py
├── embeddings/          # Embedding generation
│   └── embedding_generator.py
├── indexing/           # Vector database indexing
│   ├── document/       # Document management
│   │   ├── batch_manager.py
│   │   ├── document_processor.py
│   │   └── document_storage.py
│   ├── schema/        # Schema management
│   │   ├── schema_definition.py
│   │   ├── schema_migrator.py
│   │   └── schema_validator.py
│   ├── search/        # Search operations
│   │   ├── search_executor.py
│   │   └── search_result.py
│   ├── index/         # Core index operations
│   │   ├── index_config.py
│   │   ├── index_initializer.py
│   │   └── index_operations.py
│   └── vector_index.py # Main facade
├── utils/             # Utility functions
│   ├── cache_manager.py
│   └── logger.py
└── main.py           # Main pipeline script

tests/                # Test files
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Testing Infrastructure

### Directory Structure

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
│   │   ├── test_vector_index.py     # Core indexing tests
│   │   ├── test_document_manager.py # Document management tests
│   │   ├── test_schema_manager.py  # Schema management tests
│   │   └── test_search_manager.py  # Search functionality tests
│   ├── pipeline/         # Pipeline-specific tests
│   └── utils/           # Utility function tests
└── conftest.py          # Global fixture configuration
```

### Test Fixtures

#### Component Mocks (`fixtures/components.py`)

- `mock_weaviate_client`: Mock for Weaviate operations

  - Schema management (create_class, get, update_class)
  - Batch operations with context manager support
  - Query builder with chainable methods
  - Document CRUD operations (get_by_id, delete, update)
  - Configurable response data
  - Error simulation

- `mock_cache_manager`: Mock for caching functionality

  - get/set operations with key-value storage
  - Configurable cache hits and misses
  - TTL support
  - Error simulation for Redis operations

- `mock_doc_processor`: Document processing operations

  - Batch document processing
  - Document deduplication
  - Document merging for updates

- `mock_pii_detector`: PII detection and redaction

  - Document analysis
  - PII redaction
  - Configurable detection patterns

- `mock_topic_clusterer`: Topic clustering

  - Document clustering
  - Similar topic finding
  - Configurable clustering results

- `mock_summarizer_pipeline`: Text summarization

  - Configurable summary generation
  - Error simulation
  - Batch processing support

- `mock_openai`: OpenAI API operations
  - Embedding generation simulation
  - Configurable response vectors
  - API error simulation

#### Document Fixtures (`fixtures/documents.py`)

- `sample_document`: Basic test document with:

  - Content (body, summary)
  - Embeddings
  - Metadata
  - Relationships

- `sample_documents`: Collection of test documents
- `document_with_relationships`: Parent/child document relationships
- `large_document`: For batch processing tests

### Running Tests

```bash
# Run all tests
python -m pytest

# Run indexing tests
python -m pytest tests/unit/indexing/

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/unit/indexing/test_vector_index.py

# Run tests matching pattern
python -m pytest -k "schema"
```

### Test Configuration

#### VSCode Settings (.vscode/settings.json)

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.nosetestsEnabled": false,
  "python.testing.pytestArgs": ["tests"],
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  "python.testing.cwd": "${workspaceFolder}",
  "python.testing.debugPort": 3000,
  "python.testing.pytestPath": "pytest"
}
```

#### Pytest Configuration (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Best Practices

1. **Test Organization**

   - Group related tests in the same file
   - Use descriptive test names
   - Follow the Arrange-Act-Assert pattern

2. **Fixture Usage**

   - Use fixtures for common setup
   - Keep fixtures focused and minimal
   - Clean up resources properly

3. **Mock Configuration**

   - Mock external dependencies
   - Configure realistic mock behaviors
   - Verify mock interactions

4. **Error Handling**
   - Test both success and error paths
   - Verify error messages and logging
   - Test edge cases and boundaries

### Common Test Patterns

1. **Schema Tests**

```python
def test_ensure_schema_creation(vector_index, mock_weaviate_client):
    """Test schema creation when it doesn't exist"""
    mock_weaviate_client.schema.get.return_value = None
    vector_index.initialize()
    assert mock_weaviate_client.schema.create_class.called
    assert not mock_weaviate_client.schema.update_class.called

def test_ensure_schema_existing(vector_index, mock_weaviate_client):
    """Test schema handling when it already exists"""
    mock_weaviate_client.schema.get.return_value = {"class": "Document"}
    vector_index.initialize()
    assert not mock_weaviate_client.schema.create_class.called
```

2. **Document Operations**

```python
def test_add_documents(vector_index, mock_weaviate_client, sample_document):
    """Test adding documents to the index"""
    # Add timestamp_utc to sample document
    sample_document["metadata"]["timestamp_utc"] = datetime.now().isoformat()
    doc_ids = vector_index.add_documents([sample_document])

    assert len(doc_ids) == 1
    assert doc_ids[0] == "test-id-1"
    assert mock_weaviate_client.batch.add_data_object.called

def test_add_documents_with_deduplication(vector_index, sample_document):
    """Test document deduplication during addition"""
    # Create duplicate documents
    docs = [sample_document.copy() for _ in range(2)]
    doc_ids = vector_index.add_documents(docs, deduplicate=True)
    assert len(doc_ids) == 1  # Only one document should be added
```

3. **Cache Integration**

```python
def test_add_documents_with_cache(vector_index, mock_cache_manager, sample_document):
    """Test document addition with caching"""
    # First call should miss cache and store result
    doc_ids_1 = vector_index.add_documents([sample_document])
    assert mock_cache_manager.get.called
    assert mock_cache_manager.set.called

    # Second call should hit cache
    doc_ids_2 = vector_index.add_documents([sample_document])
    assert doc_ids_1 == doc_ids_2  # Should get same IDs from cache
```

4. **Error Handling**

```python
def test_add_documents_error(vector_index, mock_weaviate_client):
    """Test error handling in document addition"""
    mock_weaviate_client.batch.add_data_object.side_effect = Exception("Network error")

    with pytest.raises(Exception) as exc_info:
        vector_index.add_documents([{"content": "test"}])
    assert "Network error" in str(exc_info.value)
```

5. **Search Operations**

```python
def test_semantic_search(vector_index, mock_weaviate_client):
    """Test semantic search functionality"""
    query_vector = [0.1, 0.2, 0.3]
    mock_weaviate_client.query.do.return_value = {
        "data": {
            "Get": {
                "Document": [{
                    "_additional": {
                        "id": "test-id-1",
                        "distance": 0.1
                    }
                }]
            }
        }
    }

    results = vector_index.semantic_search(query_vector)
    assert len(results) == 1
    assert results[0].id == "test-id-1"
    assert mock_weaviate_client.query.with_near_vector.called
```

### Debugging Tests

1. **Verbose Output**

```bash
python -m pytest -v
```

2. **Print Statements**

```bash
python -m pytest -s
```

3. **Debug on Error**

```bash
python -m pytest --pdb
```

4. **Test Selection**

```bash
python -m pytest -k "schema" -v
```

### Test Data Management

#### Document Structure

Test documents in `tests/data/sample_documents.json` follow this structure:

```json
{
  "content": {
    "body": "Document content text",
    "summary": "Content summary",
    "title": "Document title"
  },
  "embeddings": {
    "body": [0.1, 0.2, 0.3]
  },
  "metadata": {
    "timestamp_utc": "2024-01-01T00:00:00",
    "source": "notion",
    "version": "1.0"
  },
  "relationships": {
    "parent_id": null,
    "chunk_ids": []
  }
}
```

#### Data Organization

- `tests/data/`
  - `sample_documents.json`: Basic test documents
  - `large_documents.json`: Documents for batch testing
  - `relationships.json`: Documents with parent/child relationships
  - `invalid_documents.json`: Documents for error testing

#### Version Control

- Test data is versioned with code
- Changes to data structure are documented in CHANGELOG.md
- Migration scripts provided for data updates

#### Data Generation

- Use `scripts/generate_test_data.py` for new test data
- Maintain consistent document structure
- Include edge cases and invalid data
- Document any special test cases

### Continuous Integration

#### GitHub Actions Workflow

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linting
      run: |
        pylint src tests
        black --check src tests
        isort --check-only src tests

    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

#### Coverage Requirements
- Minimum coverage: 90%
- Coverage tracked by codecov.io
- Coverage reports in PR comments

#### Performance Monitoring
- Test execution time tracked
- Performance regression alerts
- Slow test identification (>1s)

#### Quality Gates
- All tests must pass
- Coverage must meet minimum
- No linting errors
- PR review required
```

## Documentation

- [Integration Test Documentation](tests/integration/docs/README.md) - Comprehensive guide to schema integration tests
