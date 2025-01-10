"""# Source Tracking Tests

This directory contains comprehensive test suites for the document source tracking and lineage functionality. The tests cover various aspects of document processing, transformation tracking, and lineage management.

## Directory Structure

### Cross-Reference Tests

The cross-reference test suite is split into focused files following SRP:

- `test_cross_reference_basic.py`: Tests for basic chunk management

  - Adding chunks with embeddings
  - Duplicate chunk handling
  - Invalid embedding validation
  - Core functionality verification

- `test_cross_reference_validation.py`: Tests for reference validation

  - Circular reference detection
  - Orphaned reference detection
  - Missing back-reference validation
  - Valid reference structure verification

- `test_cross_reference_types.py`: Tests for reference types
  - Sequential reference management
  - Semantic similarity references
  - Topic-based clustering references
  - Reference type validation

### Alert Management Tests

The alert management test suite is split into focused files following SRP:

- `test_alert_config.py`: Tests for configuration loading and validation

  - Configuration file parsing
  - Default values
  - Invalid configuration handling
  - Threshold validation

- `test_alert_notifications.py`: Tests for notification delivery

  - Email notification handling
  - Webhook delivery
  - Failure recovery and partial success scenarios
  - Notification formatting

- `test_alert_management.py`: Tests for alert lifecycle

  - Alert ID generation and uniqueness
  - Alert history tracking
  - Cooldown mechanisms
  - Metadata preservation

- `test_alert_thresholds.py`: Tests for monitoring thresholds
  - CPU usage monitoring
  - Memory usage alerts
  - Disk space tracking
  - Resource threshold validation

### Core Test Files

- `test_document_lineage.py`: Core integration tests for document lineage functionality
- `test_basic_document_operations.py`: Tests for basic CRUD operations on documents
- `test_document_transformations.py`: Tests for document transformation tracking
- `test_document_lineage_relationships.py`: Tests for parent-child document relationships
- `test_document_processing_steps.py`: Tests for processing step tracking
- `test_document_error_logging.py`: Tests for error and warning logging

### Monitoring and Metrics

- `test_aggregated_metrics.py`: Tests for metrics aggregation and reporting
- `test_performance_metrics.py`: Tests for performance monitoring
- `test_health_check.py`: Tests for system health monitoring

### Advanced Features

- `test_version_history.py`: Tests for document version management
- `test_reliability.py`: Tests for system reliability features
- `test_source_tracking.py`: Tests for source document tracking
- `test_lineage_operations.py`: Tests for complex lineage operations

## Testing Standards

### Fixture Usage

- Common fixtures are defined in `conftest.py`
- Use the `storage` fixture for LineageStorage instances
- Use `temp_lineage_dir` for temporary test directories
- Use `test_alert_config` for alert testing configuration
- Use `sample_document` and `processed_document` for document testing
- Use `sample_embeddings` and `reference_manager` for cross-reference testing

### Test Organization

1. **Arrange**: Set up test data and prerequisites
2. **Act**: Execute the functionality being tested
3. **Assert**: Verify the results and side effects

### Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_<functionality>_<scenario>`
- Fixture functions: Descriptive names indicating purpose

### Error Testing

- Include both positive and negative test cases
- Verify error messages and exception types
- Test boundary conditions and edge cases

## Running Tests

### Basic Usage

```bash
# Run all tests in the directory
pytest tests/connectors/direct_documentation_indexing/source_tracking

# Run specific test file
pytest tests/connectors/direct_documentation_indexing/source_tracking/test_document_lineage.py

# Run with coverage
pytest --cov=src.connectors.direct_documentation_indexing.source_tracking tests/connectors/direct_documentation_indexing/source_tracking
```

### Test Options

- `-v`: Verbose output
- `-s`: Show print statements
- `-k "test_name"`: Run tests matching pattern
- `--pdb`: Debug on test failure

## Contributing

### Adding New Tests

1. Create test file following naming convention
2. Import required fixtures from conftest.py
3. Follow the Arrange-Act-Assert pattern
4. Include docstrings explaining test purpose
5. Add error cases and edge conditions

### Modifying Existing Tests

1. Maintain backwards compatibility
2. Update related test cases
3. Verify no regression in coverage
4. Update documentation if needed

## Best Practices

### Code Quality

- Keep tests focused and atomic
- Avoid test interdependencies
- Use meaningful assertions
- Include clear test descriptions

### Performance

- Clean up test data after use
- Use appropriate fixture scopes
- Minimize unnecessary I/O operations
- Group related tests appropriately

### Documentation

- Include docstrings for all test functions
- Document test prerequisites
- Explain complex test scenarios
- Update README for new features"""
