# IndexForge Models Documentation

## Document Lineage Models

### DocumentLineage

Represents the complete lineage information for a document, including its relationships and history.

```python
from src.core.tracking.models.lineage import DocumentLineage

lineage = DocumentLineage(
    doc_id="doc123",
    parents=["parent1", "parent2"],
    children=["child1"],
    derived_from="parent1",
    derived_documents=["child1", "child2"],
    metadata={
        "type": "pdf",
        "pages": 10,
        "created_at": "2024-01-17T10:00:00Z"
    },
    last_modified="2024-01-17T10:00:00Z"
)
```

**Attributes**:

- `doc_id` (str): Unique identifier for the document
- `parents` (List[str]): List of parent document IDs
- `children` (List[str]): List of child document IDs
- `derived_from` (Optional[str]): ID of the direct parent document
- `derived_documents` (List[str]): List of documents derived from this one
- `metadata` (Dict): Document metadata
- `last_modified` (str): ISO format timestamp of last modification

### Transformation

Represents a transformation operation applied to a document.

```python
from src.core.tracking.models.transformation import Transformation, TransformationType

transform = Transformation(
    type=TransformationType.CONVERSION,
    description="PDF to Text conversion",
    parameters={"format": "text", "encoding": "utf-8"},
    metadata={"processor": "pdf2text", "version": "1.0"},
    timestamp="2024-01-17T10:00:00Z"
)
```

**Attributes**:

- `type` (TransformationType): Type of transformation
- `description` (str): Description of the transformation
- `parameters` (Optional[Dict]): Parameters used in transformation
- `metadata` (Optional[Dict]): Additional metadata
- `timestamp` (str): ISO format timestamp of transformation

### TransformationType

Enumeration of supported transformation types.

```python
from src.core.tracking.models.transformation import TransformationType

class TransformationType(str, Enum):
    CONVERSION = "conversion"
    EXTRACTION = "extraction"
    MERGE = "merge"
    SPLIT = "split"
    UPDATE = "update"
```

## Storage Models

### LineageStorage

Interface for document lineage storage operations.

```python
from src.core.interfaces.storage import LineageStorage

storage = LineageStorage("/path/to/storage")
```

**Methods**:

- `get_lineage(doc_id: str) -> Optional[DocumentLineage]`
- `save_lineage(lineage: DocumentLineage) -> None`
- `get_all_lineage() -> List[DocumentLineage]`
- `delete_lineage(doc_id: str) -> None`

## Best Practices

### Document Metadata

1. **Required Fields**:

   ```python
   metadata = {
       "type": str,          # Document type (pdf, text, etc.)
       "created_at": str,    # ISO format timestamp
       "source": str,        # Origin of the document
       "version": str        # Document version
   }
   ```

2. **Optional Fields**:
   ```python
   metadata.update({
       "author": str,        # Document author
       "title": str,         # Document title
       "pages": int,         # Number of pages
       "size": int,          # File size in bytes
       "mime_type": str,     # MIME type
       "encoding": str,      # Character encoding
       "language": str,      # Document language
       "tags": List[str]     # Classification tags
   })
   ```

### Transformation Parameters

1. **Conversion Parameters**:

   ```python
   parameters = {
       "format": str,        # Target format
       "quality": str,       # Conversion quality
       "compression": str,   # Compression method
       "resolution": int     # DPI for images
   }
   ```

2. **Extraction Parameters**:
   ```python
   parameters = {
       "method": str,        # Extraction method
       "filters": List[str], # Content filters
       "threshold": float,   # Confidence threshold
       "max_length": int     # Maximum content length
   }
   ```

### Error Handling

1. **Document Not Found**:

   ```python
   if not storage.get_lineage(doc_id):
       raise ValueError(f"Document {doc_id} not found")
   ```

2. **Circular Reference**:

   ```python
   if validate_no_circular_reference(storage, parent_id, child_id):
       raise ValueError("Circular reference detected")
   ```

3. **Invalid Metadata**:
   ```python
   if not metadata.get("created_at"):
       metadata["created_at"] = datetime.now(UTC).isoformat()
   ```

## Examples

### Creating a Document Chain

```python
# Create parent document
parent = DocumentLineage(
    doc_id="parent_doc",
    metadata={
        "type": "pdf",
        "created_at": datetime.now(UTC).isoformat(),
        "source": "upload"
    }
)
storage.save_lineage(parent)

# Create child document
child = DocumentLineage(
    doc_id="child_doc",
    parents=[parent.doc_id],
    derived_from=parent.doc_id,
    metadata={
        "type": "text",
        "created_at": datetime.now(UTC).isoformat(),
        "source": "conversion"
    }
)
storage.save_lineage(child)

# Update parent with child reference
parent.children.append(child.doc_id)
parent.derived_documents.append(child.doc_id)
storage.save_lineage(parent)
```
