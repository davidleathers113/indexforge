# Mock Fixtures Documentation

## 1. Overview

### Purpose

This document describes the test fixture infrastructure used across the codebase. These fixtures provide consistent, reusable test components that simulate various parts of the system.

### Key Concepts

- **Modular Organization**: Fixtures are organized into focused modules with clear responsibilities
- **State Management**: Each module has its own state management and fixtures
- **Composition**: Higher-level fixtures compose lower-level ones to create complete test scenarios
- **Isolation**: Each module is independently usable while supporting composition

### Design Principles

1. **Single Responsibility**: Each module handles one specific aspect of testing
2. **Composability**: Fixtures can be combined for complex scenarios
3. **Consistency**: Return values and interfaces are standardized
4. **Isolation**: Tests using these fixtures should not interfere with each other

## 2. Directory Structure

```
tests/fixtures/
├── __init__.py          # Main entry point
├── constants.py         # Shared constants
├── core/               # Core functionality
│   ├── __init__.py     # Core entry point
│   ├── base.py         # Base classes
│   ├── errors.py       # Error handling
│   └── logger.py       # Logging
├── data/               # Data management
│   ├── __init__.py     # Data entry point
│   ├── cache.py        # Cache management
│   ├── embedding.py    # Embedding generation
│   └── vector.py       # Vector operations
├── documents/          # Document handling
│   ├── __init__.py     # Documents entry point
│   ├── state.py        # Document state
│   ├── processor.py    # Document processing
│   └── fixtures.py     # Sample data
├── processing/         # Processing utilities
│   ├── __init__.py     # Processing entry point
│   ├── pii.py         # PII detection
│   ├── topic.py       # Topic clustering
│   └── kmeans.py      # KMeans clustering
├── schema/            # Schema management
│   ├── __init__.py     # Schema entry point
│   ├── validator.py    # Schema validation
│   └── migrator.py     # Schema migration
├── search/            # Search functionality
│   ├── __init__.py     # Search entry point
│   ├── executor.py     # Search execution
│   └── components.py   # Search components
├── system/            # System components
│   ├── __init__.py     # System entry point
│   ├── cli.py         # CLI components
│   ├── components.py   # Component management
│   ├── monitoring.py   # System monitoring
│   └── pipeline.py     # Pipeline management
└── text/              # Text processing
    ├── __init__.py     # Text entry point
    ├── processor.py    # Text processing
    └── summarizer.py   # Text summarization
```

## 3. Module Categories

### Core Module (core/)

- Base classes and utilities
- Error handling and tracking
- Logging functionality
- **Key Fixtures:** `BaseState`, `ErrorState`, `LoggerState`

### Data Module (data/)

- Cache management
- Vector operations
- Embedding generation
- **Key Fixtures:** `CacheState`, `VectorState`, `OpenAIState`

### Documents Module (documents/)

- Document state management
- Document processing
- Sample data generation
- **Key Fixtures:** `DocumentState`, `mock_doc_processor`

### Processing Module (processing/)

- PII detection
- Topic clustering
- KMeans clustering
- **Key Fixtures:** `PIIState`, `TopicState`, `KMeansState`

### Schema Module (schema/)

- Schema validation
- Schema migration
- Version management
- **Key Fixtures:** `SchemaState`, `MigratorState`

### Search Module (search/)

- Search execution
- Search components
- Result ranking
- **Key Fixtures:** `SearchState`, `mock_search_executor`

### System Module (system/)

- CLI components
- Component management
- Monitoring and pipeline
- **Key Fixtures:** `CLIState`, `ComponentState`, `PipelineState`

### Text Module (text/)

- Text processing
- Text encoding
- Summarization
- **Key Fixtures:** `TextState`, `mock_summarizer_pipeline`

## 4. State Management

### Module States

Each module has its own state class(es) that:

- Inherit from `BaseState`
- Handle module-specific state
- Provide reset functionality
- Track errors

### State Initialization

```python
@pytest.fixture(scope="function")
def module_state():
    """Initialize module state."""
    state = ModuleState()
    yield state
    state.reset()
```

### State Usage

```python
@pytest.fixture(scope="function")
def mock_component(module_state):
    """Create mock component with state."""
    mock = MagicMock()
    mock.get_errors = module_state.get_errors
    mock.reset = module_state.reset
    yield mock
    module_state.reset()
```

## 5. Usage Examples

### Document Processing

```python
def test_document_processing(mock_doc_processor, sample_document):
    result = mock_doc_processor.process(sample_document)
    assert result["processed"] is True
```

### Pipeline Integration

```python
def test_pipeline_flow(pipeline_with_mocks, sample_documents):
    results = pipeline_with_mocks.process_documents(sample_documents)
    assert len(results) == len(sample_documents)
```

### Error Handling

```python
def test_error_handling(mock_doc_processor, mock_network_error):
    with pytest.raises(ConnectionError):
        mock_doc_processor.process_with_network()
```

## 6. Best Practices

### Module Organization

- Keep modules focused and cohesive
- Use clear entry points
- Maintain backward compatibility
- Document dependencies

### State Management

- Use module-specific state classes
- Reset state between tests
- Implement proper cleanup
- Track errors consistently

### Mock Configuration

- Keep mock behavior simple
- Match real component interfaces
- Document mock limitations
- Use consistent patterns

### Testing

- Test each module independently
- Verify module integration
- Test error scenarios
- Ensure proper cleanup

## 7. Future Improvements

### Planned Enhancements

1. Add performance testing capabilities
2. Expand error simulation
3. Add security testing
4. Improve state tracking
5. Add monitoring tools

### Documentation

1. Add module-specific guides
2. Document cross-module usage
3. Add troubleshooting guides
4. Expand best practices

### Testing

1. Add module test suites
2. Improve error coverage
3. Add performance tests
4. Test edge cases
