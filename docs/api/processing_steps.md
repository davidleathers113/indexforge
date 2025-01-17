# Processing Steps API Reference

## Overview

The Processing Steps system provides comprehensive tracking and management of document processing operations throughout their lifecycle. It enables detailed monitoring of processing status, performance metrics, and error conditions.

## Core Models

### ProcessingStatus

An enumeration representing the possible states of a processing step:

```python
from src.core.processing.steps.models.step import ProcessingStatus

ProcessingStatus.PENDING   # Initial state
ProcessingStatus.RUNNING   # Currently executing
ProcessingStatus.SUCCESS   # Completed successfully
ProcessingStatus.WARNING   # Completed with warnings
ProcessingStatus.ERROR     # Encountered a recoverable error
ProcessingStatus.FAILED    # Encountered an unrecoverable error
ProcessingStatus.SKIPPED   # Step was skipped
```

### ProcessingStep

Represents a single step in the document processing pipeline:

```python
from src.core.processing.steps.models.step import ProcessingStep

step = ProcessingStep(
    step_name="text_extraction",
    status=ProcessingStatus.SUCCESS,
    details={"chars": 5000, "pages": 10},
    metadata={
        "metrics": {"duration_ms": 1500},
        "error_message": None
    }
)
```

#### Attributes

- `step_name` (str): Identifier for the processing step
- `status` (ProcessingStatus): Current status of the step
- `details` (Dict[str, Any]): Step-specific results and data
- `metadata` (Dict[str, Any]): Additional context and metrics
- `timestamp` (datetime): When the step was executed (UTC)

#### Methods

- `to_dict()`: Convert step to dictionary format
- `from_dict(data)`: Create step from dictionary
- `duration_ms`: Get step duration in milliseconds
- `error_message`: Get error message if any
- `is_terminal_state()`: Check if step has completed
- `is_error_state()`: Check if step resulted in error

## Lifecycle Management

### ProcessingStepManager

Manages the lifecycle of processing steps across documents:

```python
from src.core.processing.steps.lifecycle.manager import ProcessingStepManager

manager = ProcessingStepManager(storage_backend)
```

#### Adding Steps

```python
manager.add_step(
    doc_id="doc123",
    step_name="text_extraction",
    status=ProcessingStatus.SUCCESS,
    details={"chars": 5000},
    metrics={"duration_ms": 1500},
    error_message=None
)
```

Parameters:

- `doc_id` (str): Document identifier
- `step_name` (str): Name of the processing step
- `status` (ProcessingStatus): Step status
- `details` (Optional[Dict]): Step-specific details
- `metrics` (Optional[Dict]): Performance metrics
- `error_message` (Optional[str]): Error description
- `timestamp` (Optional[datetime]): Step timestamp (UTC)

#### Retrieving Steps

```python
# Get all steps for a document
steps = manager.get_steps("doc123")

# Filter by status and time range
recent_errors = manager.get_steps(
    doc_id="doc123",
    status=ProcessingStatus.ERROR,
    start_time=datetime.now(UTC) - timedelta(hours=1)
)
```

Parameters:

- `doc_id` (str): Document identifier
- `status` (Optional[ProcessingStatus]): Filter by status
- `start_time` (Optional[datetime]): Include steps after this time
- `end_time` (Optional[datetime]): Include steps before this time

#### Error Aggregation

```python
# Get recent errors across all documents
errors = manager.get_recent_errors(
    since=datetime.now(UTC) - timedelta(hours=1),
    include_warnings=True
)
```

Parameters:

- `since` (datetime): Get errors after this time
- `include_warnings` (bool): Include warning status steps

## Integration Points

### Health Monitoring

The processing steps system integrates with the health monitoring system:

```python
from src.core.monitoring.health.lifecycle.manager import HealthCheckManager

health_manager = HealthCheckManager()
health_status = health_manager.perform_health_check()

# Health status reflects processing errors
if health_status.status == HealthStatus.WARNING:
    # Handle degraded performance
```

### Error Logging

Processing errors are automatically logged:

```python
from src.core.monitoring.errors.models.log_entry import LogLevel

# Errors are logged with context
manager.add_step(
    doc_id="doc123",
    step_name="image_processing",
    status=ProcessingStatus.ERROR,
    error_message="Failed to process image: corrupt file"
)
```

## Best Practices

1. **Error Handling**

   - Always provide descriptive error messages
   - Include relevant context in error details
   - Use appropriate error states (ERROR vs FAILED)

2. **Performance Monitoring**

   - Track step duration using `duration_ms`
   - Monitor resource usage in metrics
   - Set appropriate warning thresholds

3. **Concurrent Processing**

   - Use unique step names for parallel operations
   - Track step dependencies in details
   - Handle race conditions appropriately

4. **Recovery Workflows**
   - Implement retry logic for recoverable errors
   - Track retry counts in step details
   - Document recovery procedures

## Example Workflows

### Basic Processing

```python
# Start processing
manager.add_step(
    doc_id="doc123",
    step_name="processing",
    status=ProcessingStatus.RUNNING
)

try:
    # Perform processing
    result = process_document("doc123")

    # Record success
    manager.add_step(
        doc_id="doc123",
        step_name="processing",
        status=ProcessingStatus.SUCCESS,
        details=result,
        metrics={"duration_ms": 1500}
    )
except Exception as e:
    # Record failure
    manager.add_step(
        doc_id="doc123",
        step_name="processing",
        status=ProcessingStatus.ERROR,
        error_message=str(e)
    )
```

### Error Recovery

```python
def process_with_retry(doc_id: str, max_retries: int = 3) -> None:
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Attempt processing
            manager.add_step(
                doc_id=doc_id,
                step_name="processing",
                status=ProcessingStatus.RUNNING,
                details={"retry_count": retry_count}
            )

            result = process_document(doc_id)

            # Success
            manager.add_step(
                doc_id=doc_id,
                step_name="processing",
                status=ProcessingStatus.SUCCESS,
                details={"retry_count": retry_count, **result}
            )
            return

        except Exception as e:
            retry_count += 1

            if retry_count >= max_retries:
                # Final failure
                manager.add_step(
                    doc_id=doc_id,
                    step_name="processing",
                    status=ProcessingStatus.FAILED,
                    error_message=f"Max retries exceeded: {str(e)}"
                )
            else:
                # Retryable error
                manager.add_step(
                    doc_id=doc_id,
                    step_name="processing",
                    status=ProcessingStatus.ERROR,
                    error_message=f"Retry {retry_count}: {str(e)}"
                )
```

### Parallel Processing

```python
async def process_sections(doc_id: str, sections: List[str]) -> None:
    tasks = []

    for section in sections:
        # Start parallel processing
        manager.add_step(
            doc_id=doc_id,
            step_name=f"process_section_{section}",
            status=ProcessingStatus.RUNNING
        )

        # Create processing task
        task = asyncio.create_task(
            process_section(doc_id, section)
        )
        tasks.append((section, task))

    # Wait for completion
    for section, task in tasks:
        try:
            result = await task

            # Record success
            manager.add_step(
                doc_id=doc_id,
                step_name=f"process_section_{section}",
                status=ProcessingStatus.SUCCESS,
                details=result
            )

        except Exception as e:
            # Record failure
            manager.add_step(
                doc_id=doc_id,
                step_name=f"process_section_{section}",
                status=ProcessingStatus.ERROR,
                error_message=str(e)
            )
```
