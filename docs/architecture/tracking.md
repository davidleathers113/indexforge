# Document Tracking System

## Overview

The document tracking system provides comprehensive tracking of document processing history, transformations, and relationships. It follows a protocol-based design that separates interface definitions from concrete implementations, enabling flexibility and maintainability.

## Core Components

### Document Lineage

The `DocumentLineage` class serves as the central component for tracking a document's complete history:

- Origin information (source, type)
- Relationships with other documents (parents, children)
- Processing history (transformations, steps)
- Error logs and performance metrics
- Metadata and timestamps

### Protocols

Located in `src/core/models/lineage.py`, the core protocols define the interfaces for tracking components:

- `Transformation`: Records document transformations
- `ProcessingStep`: Tracks processing operations
- `LogEntry`: Manages logging information

### Implementations

Located in `src/core/tracking/models/tracking.py`, concrete implementations provide the actual tracking functionality:

```python
# Example: Recording a transformation
transform = Transformation(
    transform_type=TransformationType.CONTENT,
    description="Content extraction",
    parameters={"format": "text"}
)
document.transformations.append(transform)

# Example: Recording a processing step
step = ProcessingStep(
    step_name="text_extraction",
    status=ProcessingStatus.SUCCESS,
    details={"pages": 5}
)
document.processing_steps.append(step)

# Example: Recording an error
error = LogEntry(
    level=LogLevel.WARNING,
    message="Image skipped",
    details={"page": 3}
)
document.error_logs.append(error)
```

## Design Decisions

### Protocol-Based Design

The system uses protocols to define interfaces, providing several benefits:

1. **Separation of Concerns**: Core models define what tracking should do, while implementations define how.
2. **Flexibility**: New tracking implementations can be added without modifying core models.
3. **Testing**: Protocols enable easy mocking and testing of tracking components.

### Serialization Support

All tracking components support serialization to/from dictionaries:

- Enables easy storage and retrieval
- Maintains type safety through proper deserialization
- Handles datetime conversions automatically

### Enum-Based Types

The system uses enums for categorical data:

- `TransformationType`: Types of document transformations
- `ProcessingStatus`: Status of processing operations
- `LogLevel`: Log entry severity levels

This ensures type safety and provides clear documentation of valid values.

## Usage Guidelines

### Recording Document History

1. Create a `DocumentLineage` instance for each document
2. Add transformations as they occur
3. Record processing steps with appropriate status
4. Log errors and warnings as needed
5. Update relationships when documents are derived

### Best Practices

1. Always set appropriate status for processing steps
2. Include relevant details in transformations and logs
3. Maintain accurate parent-child relationships
4. Use appropriate log levels for different situations
5. Include timestamps for all operations

## Testing

The tracking system includes comprehensive tests:

1. Protocol compliance tests
2. Serialization/deserialization tests
3. Integration tests with DocumentLineage
4. Edge case handling

Tests are located in:

- `tests/core/tracking/models/test_tracking.py`
- `tests/core/models/test_lineage.py`
