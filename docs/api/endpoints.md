# IndexForge API Documentation

## Document Operations

### Add Document

Adds a new document to the lineage tracking system.

**Function**: `add_document`

```python
from src.core.tracking.operations import add_document

add_document(
    storage,
    doc_id="doc123",
    parent_ids=["parent1", "parent2"],
    metadata={"type": "pdf", "pages": 10}
)
```

**Parameters**:

- `storage` (LineageStorage): Storage instance for document operations
- `doc_id` (str): Unique identifier for the document
- `parent_ids` (Optional[List[str]]): List of parent document IDs
- `metadata` (Optional[Dict]): Additional document metadata

**Raises**:

- `ValueError`: If document already exists or parent documents not found
- `CircularReferenceError`: If adding parent would create circular reference

### Add Derivation

Links a derived document to its parent, establishing a lineage relationship.

**Function**: `add_derivation`

```python
from src.core.tracking.lineage.operations import add_derivation

add_derivation(
    storage,
    parent_id="parent123",
    derived_id="derived456",
    transform_type=TransformationType.CONVERSION,
    description="PDF to Text conversion",
    parameters={"format": "text", "encoding": "utf-8"},
    metadata={"processor": "pdf2text", "version": "1.0"}
)
```

**Parameters**:

- `storage` (LineageStorage): Storage instance for document operations
- `parent_id` (str): ID of the parent document
- `derived_id` (str): ID of the derived document
- `transform_type` (Optional[Union[TransformationType, str]]): Type of transformation
- `description` (str): Description of the derivation process
- `parameters` (Optional[Dict]): Parameters used in transformation
- `metadata` (Optional[Dict]): Additional metadata about the derivation

**Raises**:

- `ValueError`: If documents not found or circular reference detected

### Get Derivation Chain

Retrieves the chain of document derivations leading to a specific document.

**Function**: `get_derivation_chain`

```python
from src.core.tracking.lineage.operations import get_derivation_chain

chain = get_derivation_chain(
    storage,
    doc_id="doc123",
    max_depth=5
)
```

**Parameters**:

- `storage` (LineageStorage): Storage instance for document operations
- `doc_id` (str): ID of the document to get chain for
- `max_depth` (Optional[int]): Maximum depth to traverse

**Returns**:

- List[DocumentLineage]: Chain of documents from newest to oldest

**Raises**:

- `ValueError`: If document not found or invalid max_depth

## Document Lineage Management

### Document Lineage Manager

High-level interface for managing document transformations and relationships.

**Class**: `DocumentLineageManager`

```python
from src.core.tracking.lineage.manager import DocumentLineageManager

manager = DocumentLineageManager("/path/to/storage")
```

#### Get Transformation History

Retrieves transformation history for a document with optional filters.

```python
history = manager.get_transformation_history(
    doc_id="doc123",
    transform_type=TransformationType.CONVERSION,
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31)
)
```

**Parameters**:

- `doc_id` (str): ID of the document
- `transform_type` (Optional[Union[TransformationType, str]]): Type filter
- `start_time` (Optional[datetime]): Start time filter
- `end_time` (Optional[datetime]): End time filter

**Returns**:

- List[Transformation]: Filtered transformation history

**Raises**:

- `ValueError`: If document not found

## Validation

### Validate Lineage Relationships

Validates relationships between documents in lineage tracking.

**Function**: `validate_lineage_relationships`

```python
from src.core.tracking.lineage.operations import validate_lineage_relationships

errors = validate_lineage_relationships(lineages)
```

**Parameters**:

- `lineages` (List[DocumentLineage]): Documents to validate

**Returns**:

- List[str]: Error messages, empty if no errors found

## Best Practices

1. **Document IDs**:

   - Use consistent, unique identifiers
   - Prefer descriptive but concise IDs
   - Include version or timestamp if relevant

2. **Metadata**:

   - Include creation timestamp
   - Add source information
   - Document content type
   - Include processing context

3. **Error Handling**:

   - Always check for circular references
   - Validate document existence
   - Handle missing parent/child references
   - Log validation errors

4. **Performance Considerations**:
   - Limit derivation chain depth
   - Batch process related documents
   - Use appropriate indexing
   - Monitor storage usage

## Examples

### Complete Document Processing Flow

```python
from src.core.tracking.lineage.manager import DocumentLineageManager
from src.core.tracking.models.transformation import TransformationType

# Initialize manager
manager = DocumentLineageManager()

# Add original document
doc_id = "original_doc"
manager.add_document(
    doc_id=doc_id,
    metadata={
        "type": "pdf",
        "pages": 10,
        "source": "user_upload"
    }
)

# Process and create derived document
derived_id = "processed_doc"
manager.add_document(
    doc_id=derived_id,
    parent_ids=[doc_id],
    metadata={
        "type": "text",
        "processor": "pdf2text",
        "version": "1.0"
    }
)

# Add derivation details
add_derivation(
    manager.storage,
    parent_id=doc_id,
    derived_id=derived_id,
    transform_type=TransformationType.CONVERSION,
    description="PDF to text conversion",
    parameters={"format": "text", "quality": "high"},
    metadata={"processor_version": "1.0"}
)

# Validate relationships
lineages = [
    manager.storage.get_lineage(doc_id),
    manager.storage.get_lineage(derived_id)
]
errors = validate_lineage_relationships(lineages)
if errors:
    print("Validation errors:", errors)
```
