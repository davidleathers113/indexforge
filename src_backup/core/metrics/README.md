# Service Metrics Collection System

## Overview

A comprehensive metrics collection and monitoring system for tracking service performance, resource utilization, and operational health. The system provides real-time insights into service behavior and supports performance optimization.

## Features

- Operation timing and performance tracking
- Memory usage monitoring
- Error rate calculation
- Health check capabilities
- Performance profiling
- Resource utilization tracking
- Batch operation monitoring
- Service-specific metrics

## Quick Start

```python
from src.core.metrics import ServiceMetricsCollector

# Initialize collector
metrics = ServiceMetricsCollector(
    service_name="my_service",
    max_history=1000,
    memory_threshold_mb=500
)

# Track operations
with metrics.measure_operation("my_operation", metadata={"key": "value"}):
    # Your operation code here
    perform_task()

# Get metrics
current_metrics = metrics.get_current_metrics()
health_status = metrics.check_health()
```

## Core Components

### ServiceMetricsCollector

The main class for metrics collection and analysis. Provides:

- Operation tracking via context manager
- Metrics aggregation and analysis
- Health monitoring
- Resource usage tracking
- Performance profiling

### OperationMetrics

Data class for storing individual operation metrics:

- Operation timing
- Memory usage
- Success/failure status
- Error information
- Custom metadata

## Integration

The system is integrated with:

1. Redis Service

   - Pipeline operations
   - Cache performance
   - Connection health

2. Weaviate Service
   - Batch operations
   - Vector search performance
   - Resource utilization

## Testing

Comprehensive test suite available:

```bash
# Run unit tests
pytest tests/unit/core/test_metrics.py

# Run performance tests
pytest tests/performance/test_performance.py
```

## Best Practices

1. Operation Naming

   - Use descriptive names
   - Include context
   - Follow conventions

2. Resource Management

   - Monitor thresholds
   - Clean up properly
   - Use batching

3. Performance Monitoring
   - Track key metrics
   - Set up alerts
   - Monitor trends

## Documentation

For detailed documentation, see:

- [Metrics and Performance Guide](../../docs/metrics_and_performance.md)
- [API Reference](../../docs/api_reference.md)
- [Performance Testing Guide](../../docs/performance_testing.md)

## Contributing

When contributing:

1. Follow coding standards
2. Add tests for new features
3. Update documentation
4. Run performance tests

## License

This component is part of the main project and follows its licensing terms.
