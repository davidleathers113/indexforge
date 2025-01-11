# Testing Standards and Best Practices

## Core Principles

### Single Responsibility (SRP)

- Each test file should focus on testing ONE specific component or behavior
- Test files should be named descriptively: `test_<component>_<behavior>.py`. For example:
  - `test_batch_metrics_recording.py`
  - `test_batch_metrics_errors.py`
- Each test function should verify ONE specific aspect or scenario. Examples include:
  - `test_record_batch_completion_increments_counter()`
  - `test_record_batch_error_updates_error_types()`
- Keep test functions focused and atomic. Avoid testing multiple behaviors in one function.

### Separation of Concerns

- Separate test setup from assertions:
  - Use fixtures for reusable setup and teardown logic
  - Place mock setup and assertions in different sections of the test
- Keep test data separate from test logic. Use constants or fixtures to manage test inputs
- Isolate external dependencies using mocks and test doubles
- Example of separating setup from assertions:

  ```python
  @pytest.fixture
  def mock_collection():
      return Mock(spec=Collection)

  def test_batch_processing(mock_collection):
      # Arrange
      mock_collection.batch.add_object.return_value = True

      # Act
      result = process_batch(mock_collection, items=[{"id": 1}])

      # Assert
      assert result.success is True
  ```

### Modularity

- Each test should be independent and self-contained
- No dependencies between test cases
- No shared state between tests
- Tests should be runnable in any order (use pytest's --random-order)

### Size and Complexity

- Keep test files under 100 lines
- Maximum 5-7 test functions per file
- Maximum 10 lines per test function (excluding setup)
- Use helper functions for complex setup

## File Organization

```
tests/
├── unit/
│   ├── operations/
│   │   ├── base/
│   │   │   ├── test_batch_operation_execute.py
│   │   │   ├── test_batch_operation_error_handling.py
│   │   │   └── test_batch_operation_validation.py
│   │   ├── states/
│   │   │   ├── test_initial_state_tracking.py
│   │   │   ├── test_processing_state_success.py
│   │   │   └── test_processing_state_errors.py
│   │   └── ...
│   ├── metrics/
│   │   ├── test_batch_metrics_recording.py
│   │   ├── test_batch_metrics_errors.py
│   │   └── test_performance_tracking.py
│   └── ...
├── integration/
└── performance/
```

## Test Structure

### File Template

```python
"""Test specific behavior of component."""

import pytest
from unittest.mock import Mock

from src.api.repositories.weaviate.metrics import BatchPerformanceTracker

# Constants for test data
TEST_DATA = {
    "valid_batch": {
        "size": 50,
        "successful": 95,
        "failed": 5
    },
    "error_batch": {
        "size": 50,
        "successful": 40,
        "failed": 60
    }
}

@pytest.fixture
def tracker():
    """Setup BatchPerformanceTracker with test configuration."""
    return BatchPerformanceTracker(
        min_batch_size=10,
        max_batch_size=100,
        window_size=5
    )

def test_optimize_increases_size_on_success(tracker):
    """
    Test batch size increases when error rate is low.

    Given: A tracker with initial batch size of 50
    When: Processing a batch with high success rate
    Then: The optimal batch size should increase
    """
    # Arrange
    batch = TEST_DATA["valid_batch"]
    tracker.start_batch(batch["size"])

    # Act
    tracker.end_batch(
        successful_objects=batch["successful"],
        failed_objects=batch["failed"]
    )

    # Assert
    assert tracker.get_optimal_batch_size() > batch["size"], (
        f"Expected batch size to increase from {batch['size']}"
    )
```

## Testing Standards

### Naming Conventions

- Test files: `test_<component>_<behavior>.py`
  - Example: `test_batch_metrics_recording.py`
- Test functions: `test_<scenario>_<expected_outcome>`
  - Example: `test_record_batch_completion_updates_counters()`
- Test classes (if needed): `Test<Component><Behavior>`
  - Example: `TestBatchMetricsRecording`
- Fixtures: `setup_<component>` or `mock_<dependency>`
  - Example: `setup_batch_metrics`, `mock_collection`

### Documentation

- Each test file must have a docstring explaining what it tests
- Each test function must have a docstring describing:
  - Given: Initial conditions and setup
  - When: Action being tested
  - Then: Expected outcome and assertions
  - Any important assumptions

### Assertions

- Use explicit assertions with meaningful messages:
  ```python
  assert result.success is True, f"Expected success but got {result.error}"
  ```
- One logical assertion per test
- Use pytest's built-in assertions
- Include context in assertion messages

### Mocking

- Mock external dependencies (Weaviate client, collections)
- Use pytest-mock fixtures
- Keep mock setup in fixtures
- Verify mock interactions when they're part of the behavior:
  ```python
  mock_collection.batch.add_object.assert_called_once_with(
      properties=expected_properties
  )
  ```

### Data Management

- Use small, focused test data sets
- Keep test data in separate files/fixtures
- Use factory functions for complex objects
- Clean up test data in fixture teardown

### Error Testing

- Test both success and error paths
- Verify error messages and types:
  ```python
  with pytest.raises(BatchProcessingError, match="Validation failed"):
      batch.process(invalid_data)
  ```
- Test boundary conditions
- Test edge cases explicitly

## Best Practices

### DO

- Write tests before fixing bugs
- Keep tests simple and readable
- Use meaningful variable names
- Follow Arrange-Act-Assert pattern
- Clean up resources in fixtures
- Test public interfaces
- Use type hints in test code
- Log test failures clearly

### DON'T

- Share state between tests
- Make unnecessary assertions
- Use sleep() in tests
- Test implementation details
- Write tests that depend on timing
- Create complex test hierarchies
- Use global variables
- Write tests that depend on others

### Performance

- Keep tests fast (< 100ms)
- Use setup_class for slow setup
- Mock slow operations
- Use parametrize for multiple cases
- Profile slow test suites

### Maintainability

- Review tests during code review
- Keep test code as clean as production code
- Refactor tests when needed
- Delete obsolete tests
- Update tests when requirements change

## Review Checklist

Before submitting test code, verify:

### Style

- [ ] Tests follow SRP
- [ ] File is under 100 lines
- [ ] Code is properly formatted

### Structure

- [ ] Tests are independent
- [ ] Mocks are appropriate
- [ ] Fixtures are used effectively

### Coverage

- [ ] Error cases are covered
- [ ] Edge cases are tested
- [ ] Assertions are meaningful

### Documentation

- [ ] File docstring is clear
- [ ] Function docstrings follow Given-When-Then
- [ ] Comments explain complex setup

### Performance

- [ ] Tests run quickly
- [ ] Resources are cleaned up
- [ ] No unnecessary operations
