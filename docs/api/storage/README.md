# Storage System API Documentation

## Overview

The storage system provides a flexible, type-safe, and thread-safe implementation for managing document storage and lineage tracking. It follows a layered architecture with clear separation of concerns:

- **Storage Strategies**: Implementations for different storage backends
- **Repositories**: Type-safe document and lineage management
- **Metrics**: Performance and health monitoring

## Storage Strategies

### Base Protocol

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class StorageStrategy(Generic[T]):
    """Base protocol for storage implementations."""

    def save(self, key: str, data: T) -> None: ...
    def load(self, key: str) -> T: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
```

### Memory Storage

```python
# Fast, thread-safe storage for testing
storage = MemoryStorage(Document, simulate_failures=False)

# Basic operations
storage.save("doc1", document)
loaded = storage.load("doc1")
storage.delete("doc1")
```

### Error Handling

```python
try:
    data = storage.load("missing")
except DataNotFoundError:
    logger.warning("Document not found")
except DataCorruptionError:
    logger.error("Data corruption detected")
except StorageError as e:
    logger.error("Storage operation failed: %s", e)
```

## Repositories

### Document Repository

```python
# Initialize with storage strategy
repo = DocumentRepository(storage_strategy)

# CRUD operations
doc = Document(id="doc1", content="test")
repo.create(doc)
repo.update(doc)
repo.delete(doc.id)
```

### Lineage Repository

```python
# Track document lineage
lineage_repo = LineageRepository(storage_strategy)

# Record lineage
lineage = DocumentLineage(
    doc_id="doc1",
    origin_id="original",
    transformations=["cleaned", "normalized"]
)
lineage_repo.save(lineage)

# Query by time range
recent = lineage_repo.get_by_time_range(
    start_time=datetime.now() - timedelta(hours=1)
)
```

## Metrics Collection

```python
# Initialize collector
collector = MetricsCollector()

# Record operations
with collector.track_operation("save"):
    repo.save(document)

# Get metrics
metrics = collector.get_metrics()
print(f"Average latency: {metrics.avg_latency_ms}ms")
```

## Best Practices

1. **Type Safety**

   - Always use type hints
   - Validate data with Pydantic models
   - Handle type errors explicitly

2. **Thread Safety**

   - Use storage methods directly (thread-safe)
   - Avoid external synchronization
   - Monitor concurrent access patterns

3. **Error Handling**

   - Catch specific exceptions
   - Log errors with context
   - Maintain error hierarchies

4. **Performance**
   - Monitor metrics
   - Use batch operations when possible
   - Consider caching strategies

## Migration Guide

1. **Replace Direct Storage**

   ```python
   # Old: Direct file operations
   with open(path, "w") as f:
       json.dump(data, f)

   # New: Use storage strategy
   storage.save(key, data)
   ```

2. **Update Error Handling**

   ```python
   # Old: Generic exceptions
   try:
       process_document()
   except Exception as e:
       log_error(e)

   # New: Specific exceptions
   try:
       repo.process_document()
   except DocumentNotFoundError:
       handle_missing_document()
   except StorageError as e:
       handle_storage_error(e)
   ```

3. **Integrate Metrics**

   ```python
   # Old: Manual timing
   start = time.perf_counter()
   process()
   duration = time.perf_counter() - start

   # New: Metrics collector
   with collector.track_operation("process"):
       repo.process()
   ```
