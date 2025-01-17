# Document Tracking API Reference

This document provides detailed API documentation for the document tracking and lineage functionality.

## Document Operations

### add_document

Adds a new document to the lineage tracking system.

```python
def add_document(
    storage: LineageStorage,
    doc_id: str,
    parent_ids: Optional[List[str]] = None,
    origin_id: Optional[str] = None,
    origin_source: Optional[str] = None,
    origin_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None
```

#### Parameters

- `storage`: LineageStorage instance for persistence
- `doc_id`: Unique identifier for the document
- `parent_ids`: Optional list of parent document IDs to establish lineage
- `origin_id`: Optional identifier from the source system
- `origin_source`: Optional identifier for the source system
- `origin_type`: Optional document type classification
- `metadata`: Optional dictionary of additional document metadata

#### Raises

- `ValueError`: If document already exists, parent not found, or would create circular reference

#### Example

```python
from src.core.interfaces.storage import LineageStorage
from src.core.tracking.operations import add_document

# Initialize storage
storage = LineageStorage()

# Add a document with metadata
add_document(
    storage=storage,
    doc_id="doc123",
    parent_ids=["parent1", "parent2"],
    origin_id="original_doc",
    origin_source="external_system",
    origin_type="pdf",
    metadata={"author": "John Doe", "created_at": "2024-01-17"}
)
```

## Lineage Operations

### add_derivation

Links a derived document to its parent, establishing a lineage relationship.

```python
def add_derivation(
    storage: LineageStorage,
    parent_id: str,
    derived_id: str,
    transform_type: Optional[Union[TransformationType, str]] = None,
    description: str = "",
    parameters: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> None
```

#### Parameters

- `storage`: LineageStorage instance
- `parent_id`: ID of the parent document
- `derived_id`: ID of the derived document
- `transform_type`: Type of transformation applied
- `description`: Description of the derivation
- `parameters`: Parameters used in the transformation
- `metadata`: Additional metadata about the derivation

#### Raises

- `ValueError`: If parent or derived document not found, or if circular reference detected

#### Example

```python
from src.core.tracking.lineage.operations import add_derivation
from src.core.tracking.models.transformation import TransformationType

# Add a derivation relationship
add_derivation(
    storage=storage,
    parent_id="original_doc",
    derived_id="processed_doc",
    transform_type=TransformationType.CHUNKING,
    description="Document chunking for improved processing",
    parameters={"chunk_size": 1000},
    metadata={"processor_version": "1.0.0"}
)
```

### get_derivation_chain

Retrieves the derivation chain for a document.

```python
def get_derivation_chain(
    storage: LineageStorage,
    doc_id: str,
    max_depth: Optional[int] = None,
) -> List[DocumentLineage]
```

#### Parameters

- `storage`: LineageStorage instance
- `doc_id`: ID of the document to trace
- `max_depth`: Optional maximum depth to traverse

#### Returns

- List of DocumentLineage objects representing the derivation chain

#### Example

```python
from src.core.tracking.lineage.operations import get_derivation_chain

# Get derivation chain
chain = get_derivation_chain(
    storage=storage,
    doc_id="processed_doc",
    max_depth=5
)
```

## Validation

### validate_lineage_relationships

Validates a set of lineage relationships for circular references and other constraints.

```python
def validate_lineage_relationships(
    lineages: List[DocumentLineage]
) -> List[str]
```

#### Parameters

- `lineages`: List of DocumentLineage objects to validate

#### Returns

- List of validation error messages (empty if validation passes)

#### Example

```python
from src.core.tracking.lineage.operations import validate_lineage_relationships

# Validate lineage relationships
errors = validate_lineage_relationships(chain)
if errors:
    print("Validation errors found:", errors)
```
