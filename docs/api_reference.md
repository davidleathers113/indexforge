# API Reference

## ServiceMetricsCollector

### Constructor

```python
ServiceMetricsCollector(
    service_name: str,
    max_history: int = 1000,
    memory_threshold_mb: float = 500,
) -> None
```

Creates a new metrics collector instance.

**Parameters:**

- `service_name`: Name of the service being monitored
- `max_history`: Maximum number of operations to keep in history (default: 1000)
- `memory_threshold_mb`: Memory usage threshold in MB (default: 500)

### Methods

#### measure_operation

```python
@contextmanager
def measure_operation(
    operation_name: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None
```

Context manager for measuring operation performance.

**Parameters:**

- `operation_name`: Name of the operation to measure
- `metadata`: Optional dictionary of operation metadata

**Example:**

```python
with metrics.measure_operation("my_operation", {"batch_size": 100}):
    process_batch()
```

#### get_current_metrics

```python
def get_current_metrics() -> Dict[str, Any]
```

Get current service metrics.

**Returns:**
Dictionary containing:

- `service_name`: Service identifier
- `total_operations`: Total operation count
- `error_rate`: Current error rate
- `avg_duration`: Average operation duration
- `max_duration`: Maximum operation duration
- `avg_memory_mb`: Average memory usage
- `max_memory_mb`: Maximum memory usage
- `operation_counts`: Operation frequency counts
- `error_counts`: Error frequency counts
- `slow_operations`: List of slow operations

#### get_operation_metrics

```python
def get_operation_metrics(
    operation_name: str,
    time_window: Optional[timedelta] = None,
) -> Dict[str, Any]
```

Get metrics for a specific operation.

**Parameters:**

- `operation_name`: Name of the operation
- `time_window`: Optional time window for filtering metrics

**Returns:**
Dictionary containing:

- `operation_name`: Operation identifier
- `total_calls`: Total number of calls
- `error_rate`: Operation error rate
- `avg_duration`: Average duration
- `max_duration`: Maximum duration
- `avg_memory_mb`: Average memory usage
- `max_memory_mb`: Maximum memory usage
- `success_rate`: Operation success rate

#### check_health

```python
def check_health() -> Dict[str, Any]
```

Check service health status.

**Returns:**
Dictionary containing:

- `status`: Overall health status ("healthy", "warning", "unknown")
- `timestamp`: Check timestamp
- `checks`: Dictionary of specific health checks
  - `memory_usage`: Memory usage check
  - `error_rate`: Error rate check
  - `performance`: Performance check

#### reset

```python
def reset() -> None
```

Reset all metrics collections.

## OperationMetrics

### Constructor

```python
@dataclass
class OperationMetrics:
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = True
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    memory_usage: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

Data class for storing operation metrics.

**Fields:**

- `operation_name`: Name of the operation
- `start_time`: Operation start time
- `end_time`: Operation end time
- `duration`: Operation duration in seconds
- `success`: Whether operation succeeded
- `error_type`: Type of error if failed
- `error_message`: Error message if failed
- `memory_usage`: Memory usage in MB
- `metadata`: Custom operation metadata

## Service Integration

### Redis Service

```python
class RedisService:
    def get_metrics(self) -> Dict[str, Any]
    def get_health(self) -> Dict[str, Any]
```

### Weaviate Service

```python
class WeaviateClient:
    def get_metrics(self) -> Dict[str, Any]
    def get_health(self) -> Dict[str, Any]
```

## Type Definitions

```python
CacheValue = Union[str, int, float, bytes, List[Any], Dict[str, Any]]
PipelineOperation = Tuple[str, str, List[Any]]  # command, key, args
```

## Constants

```python
DEFAULT_MAX_HISTORY = 1000
DEFAULT_MEMORY_THRESHOLD_MB = 500
SLOW_OPERATION_THRESHOLD = 0.1  # seconds
ERROR_RATE_THRESHOLD = 0.05  # 5%
```

## Error Handling

The metrics system uses Python's built-in exception handling. Common exceptions:

- `ValueError`: Invalid parameter values
- `RuntimeError`: Operation context errors
- `MemoryError`: Memory threshold exceeded

## Performance Considerations

1. Memory Usage

   - Metrics are stored in memory
   - History is limited by max_history
   - Old metrics are automatically removed

2. Thread Safety

   - Context manager is thread-safe
   - Metrics collection is atomic
   - Reset operation is thread-safe

3. Resource Management
   - Automatic cleanup of old metrics
   - Memory usage monitoring
   - Resource leak prevention
