# Storage System Usage Examples

## Basic Operations

### Document Storage

```python
from uuid import uuid4
from datetime import datetime, UTC
from src.core.models.documents import Document
from src.core.storage.strategies.memory_storage import MemoryStorage
from src.core.storage.repositories.documents import DocumentRepository

# Initialize storage and repository
storage = MemoryStorage(Document)
repo = DocumentRepository(storage)

# Create a document
doc = Document(
    id=str(uuid4()),
    content="Example document",
    created_at=datetime.now(UTC),
    metadata={"source": "user_upload"}
)

# Save document
repo.create(doc)

# Retrieve document
loaded_doc = repo.get(doc.id)

# Update document
doc.metadata["status"] = "processed"
repo.update(doc)

# Delete document
repo.delete(doc.id)
```

## Advanced Scenarios

### Batch Processing

```python
from typing import List
from src.core.storage.repositories.documents import DocumentRepository

def process_documents(repo: DocumentRepository, docs: List[Document]) -> None:
    """Process multiple documents efficiently."""
    # Save all documents
    for doc in docs:
        repo.create(doc)

    # Process in batches
    batch_size = 100
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        for doc in batch:
            doc.metadata["processed"] = True
            repo.update(doc)

# Usage
docs = [create_document() for _ in range(1000)]
process_documents(repo, docs)
```

### Error Recovery

```python
from src.core.storage.strategies.base import DataNotFoundError, StorageError
from src.core.monitoring.errors.manager import ErrorManager

def safe_process_document(repo: DocumentRepository, doc_id: str) -> None:
    """Process document with error recovery."""
    error_manager = ErrorManager()

    try:
        doc = repo.get(doc_id)
        process_document(doc)
        repo.update(doc)
    except DataNotFoundError:
        error_manager.log_error(
            "Document not found",
            doc_id=doc_id,
            severity="warning"
        )
    except StorageError as e:
        error_manager.log_error(
            "Storage error",
            doc_id=doc_id,
            error=str(e),
            severity="error"
        )
        # Attempt recovery
        if should_retry(e):
            retry_process_document(doc_id)
```

### Concurrent Access

```python
import threading
from src.core.storage.repositories.documents import DocumentRepository
from src.core.monitoring.metrics.collector import MetricsCollector

class DocumentProcessor:
    def __init__(self, repo: DocumentRepository):
        self.repo = repo
        self.metrics = MetricsCollector()
        self._lock = threading.Lock()

    def process_concurrent(self, doc_ids: List[str]) -> None:
        """Process documents concurrently."""
        def worker(doc_id: str) -> None:
            try:
                with self.metrics.track_operation("process"):
                    doc = self.repo.get(doc_id)
                    self._process_single(doc)
                    self.repo.update(doc)
            except Exception as e:
                with self._lock:
                    self.metrics.record_error("process", str(e))

        # Start worker threads
        threads = []
        for doc_id in doc_ids:
            thread = threading.Thread(target=worker, args=(doc_id,))
            thread.start()
            threads.append(thread)

        # Wait for completion
        for thread in threads:
            thread.join()

# Usage
processor = DocumentProcessor(repo)
processor.process_concurrent(["doc1", "doc2", "doc3"])
```

### Document Lineage Tracking

```python
from src.core.storage.repositories.lineage import LineageRepository
from src.core.models.lineage import DocumentLineage

def track_document_processing(
    doc_repo: DocumentRepository,
    lineage_repo: LineageRepository,
    doc_id: str
) -> None:
    """Track document processing with lineage."""
    # Get original document
    doc = doc_repo.get(doc_id)

    # Create lineage record
    lineage = DocumentLineage(
        doc_id=doc_id,
        origin_id=doc_id,
        transformations=[],
        processing_steps=[]
    )

    # Process document
    try:
        # Apply transformation
        doc = transform_document(doc)
        lineage.transformations.append("normalized")

        # Update document
        doc_repo.update(doc)

        # Record processing step
        lineage.processing_steps.append({
            "name": "normalization",
            "status": "success",
            "timestamp": datetime.now(UTC)
        })
    except Exception as e:
        # Record failure
        lineage.processing_steps.append({
            "name": "normalization",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now(UTC)
        })
    finally:
        # Save lineage
        lineage_repo.save(lineage)
```

## Performance Optimization

### Caching Strategy

```python
from functools import lru_cache
from src.core.storage.repositories.documents import DocumentRepository

class CachedDocumentRepository:
    def __init__(self, repo: DocumentRepository, cache_size: int = 100):
        self.repo = repo
        self._get_cached = lru_cache(maxsize=cache_size)(self._get)

    def _get(self, doc_id: str) -> Document:
        return self.repo.get(doc_id)

    def get(self, doc_id: str) -> Document:
        return self._get_cached(doc_id)

    def update(self, doc: Document) -> None:
        # Invalidate cache on update
        self._get_cached.cache_clear()
        self.repo.update(doc)

# Usage
cached_repo = CachedDocumentRepository(repo)
doc = cached_repo.get("doc1")  # First access: hits storage
same_doc = cached_repo.get("doc1")  # Second access: hits cache
```

### Metrics Monitoring

```python
from src.core.monitoring.metrics.collector import MetricsCollector
from src.core.monitoring.alerts.manager import AlertManager

def monitor_storage_performance(
    repo: DocumentRepository,
    collector: MetricsCollector,
    alert_manager: AlertManager
) -> None:
    """Monitor storage performance with alerts."""
    # Track operation metrics
    with collector.track_operation("bulk_process"):
        process_documents(repo, generate_test_docs(1000))

    # Get metrics
    metrics = collector.get_metrics()

    # Check thresholds
    if metrics.avg_latency_ms > 100:
        alert_manager.send_alert(
            "High latency detected",
            severity="warning",
            metrics=metrics
        )

    if metrics.error_rate > 0.01:
        alert_manager.send_alert(
            "High error rate detected",
            severity="error",
            metrics=metrics
        )
```
