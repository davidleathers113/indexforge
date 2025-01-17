"""Document Lineage API Documentation

This document describes the document lineage tracking functionality, which manages relationships and history between documents.

## Core Concepts

### Document Lineage

Document lineage tracks relationships between documents, including:

- Parent-child relationships
- Derivation chains
- Processing history
- Transformation records

## API Reference

### Storage Operations

#### DocumentStorage

```python
from src.core.tracking.storage import DocumentStorage
from src.core.models.settings import Settings

storage = DocumentStorage(storage_path="/path/to/storage", settings=Settings(...))
```

**Methods**:

- `get_document(doc_id: UUID) -> Optional[Document]`

  - Retrieves a document by ID
  - Returns None if not found

- `save_document(document: Document) -> None`

  - Saves a new document or updates existing
  - Validates document type and relationships
  - Updates timestamps automatically

- `update_document(doc_id: UUID, updates: Dict[str, Any]) -> None`

  - Updates specific document fields
  - Handles metadata, status, relationships
  - Maintains bidirectional relationships
  - Validates updates for consistency

- `delete_document(doc_id: UUID) -> None`
  - Removes document from storage
  - Raises KeyError if not found

### Document Relationships

#### Parent-Child Relationships

```python
# Create parent document
parent = Document(
    metadata=DocumentMetadata(
        title="Parent Doc",
        doc_type=DocumentType.PDF
    ),
    id=uuid4()
)
storage.save_document(parent)

# Create child document
child = Document(
    metadata=DocumentMetadata(
        title="Child Doc",
        doc_type=DocumentType.TEXT
    ),
    id=uuid4(),
    parent_id=parent.id
)
storage.save_document(child)
```

#### Update Relationships

```python
# Add new parent
storage.update_document(doc_id, {
    "parent_id": new_parent_id
})

# Update children
storage.update_document(doc_id, {
    "child_ids": [child1_id, child2_id]
})
```

### Document Metadata

```python
# Update metadata
storage.update_document(doc_id, {
    "metadata": {
        "title": "Updated Title",
        "language": "fr",
        "custom_metadata": {"key": "value"}
    }
})
```

### Status Management

```python
# Update document status
storage.update_document(doc_id, {
    "status": DocumentStatus.PROCESSED
})
```

### Error Handling

```python
try:
    storage.update_document(doc_id, updates)
except KeyError:
    # Document not found
    ...
except ValueError as e:
    # Invalid update (e.g., invalid type, circular reference)
    ...
```

## Best Practices

1. **Relationship Management**

   - Always maintain bidirectional relationships
   - Avoid circular references
   - Update both parent and child documents

2. **Type Safety**

   - Use proper DocumentType enums
   - Validate metadata types
   - Handle optional fields appropriately

3. **Error Handling**

   - Check for document existence
   - Validate updates before applying
   - Handle relationship conflicts

4. **Performance**
   - Use batch operations for multiple updates
   - Monitor metrics for operation timing
   - Implement proper cleanup

## Examples

### Creating Document Chain

```python
def create_document_chain(storage: DocumentStorage, titles: List[str]) -> List[UUID]:
    """Create a chain of related documents."""
    doc_ids = []
    parent_id = None

    for title in titles:
        doc = Document(
            metadata=DocumentMetadata(
                title=title,
                doc_type=DocumentType.TEXT
            ),
            id=uuid4(),
            parent_id=parent_id
        )
        storage.save_document(doc)
        doc_ids.append(doc.id)
        parent_id = doc.id

    return doc_ids
```

### Validating Relationships

```python
def validate_document_relationships(storage: DocumentStorage, doc_id: UUID) -> bool:
    """Validate document relationships are consistent."""
    doc = storage.get_document(doc_id)
    if not doc:
        return False

    # Check parent relationship
    if doc.parent_id:
        parent = storage.get_document(doc.parent_id)
        if not parent or doc.id not in parent.child_ids:
            return False

    # Check child relationships
    for child_id in doc.child_ids:
        child = storage.get_document(child_id)
        if not child or child.parent_id != doc.id:
            return False

    return True
```

## Metrics and Monitoring

The storage system includes built-in metrics collection:

```python
# Get operation metrics
metrics = storage.metrics.get_metrics()

# Average operation duration
avg_save_time = storage.metrics.get_average_duration("save_document")
avg_update_time = storage.metrics.get_average_duration("update_document")
```

## Migration Guide

When migrating from the old source tracking system:

1. Create new DocumentStorage instance
2. Copy existing documents with proper typing
3. Validate relationships after migration
4. Update application code to use new API
5. Remove old source tracking code

## Security Considerations

1. **Access Control**

   - Implement proper authentication
   - Validate document ownership
   - Control relationship modifications

2. **Data Validation**

   - Sanitize metadata input
   - Validate document types
   - Check relationship permissions

3. **Error Prevention**
   - Prevent circular references
   - Validate parent-child relationships
   - Handle concurrent modifications
