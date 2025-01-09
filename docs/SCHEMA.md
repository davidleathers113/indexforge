# **Weaviate Schema Documentation**

_Integration Note: We retained the detailed, technical descriptions from Report A (e.g., table structures, schema configuration parameters) and combined them with the more user-friendly explanations and formatting from Report B._

---

## **1. Introduction**

This document provides a comprehensive overview of a Weaviate schema designed for **document indexing** and **semantic search**. It aims to store, retrieve, and semantically query documents with vector embeddings, while also preserving relationships between **document chunks** and **versions**. By utilizing both **vector-based** and **keyword-based** search methods, the schema ensures **scalability** and **flexibility** for various use cases.

_Integration Note: The introduction from Report B offered a concise statement of purpose, which we’ve combined with the explicit mention of chunk relationships and versions emphasized in Report A._

---

## **2. Schema Overview**

### **2.1 Class Definition**

The schema defines a single class, **`Document`**, which represents the documents to be indexed and searched. Below is the core configuration:

```json
{
  "class": "Document",
  "description": "A document with vector embeddings",
  "vectorizer": "text2vec-transformers",
  "moduleConfig": {
    "text2vec-transformers": {
      "model": "sentence-transformers-all-MiniLM-L6-v2",
      "poolingStrategy": "mean",
      "vectorizeClassName": false,
      "maxTokens": 512
    }
  }
}
```

- **Vectorizer:** Utilizes `text2vec-transformers` to generate vector embeddings.
- **Model:** `sentence-transformers-all-MiniLM-L6-v2`, chosen for a good balance between **performance** and **computational efficiency**.
- **Pooling Strategy:** `mean`, which averages token embeddings to create a single vector for the entire document.
- **vectorizeClassName:** Set to `false` to avoid adding the class name into the vector representation.
- **maxTokens:** Caps the text input at 512 tokens to fit within the model’s constraints.

_Integration Note: We have taken the thorough property definitions from Report A and included the user-friendly explanations from Report B._

---

## **3. Properties**

The `Document` class includes **Content**, **Embedding**, and **Metadata** properties.

### **3.1 Content Properties**

| Property          | Data Type | Description           | Vectorization  | Notes                    |
| ----------------- | --------- | --------------------- | -------------- | ------------------------ |
| `content_body`    | `text`    | Main document content | **Vectorized** | Used for semantic search |
| `content_summary` | `text`    | Document summary      | Not vectorized | Quick content preview    |
| `content_title`   | `text`    | Document title        | Not vectorized | Document identification  |

- **content_body**: The full text of the document, vectorized for semantic searches.
- **content_summary**: A concise summary; helps in quick previews or abstracts.
- **content_title**: The title or name of the document, helpful for quick identification.

_Integration Note: We merged the high-level table format from Report A and the explanatory text from Report B._

### **3.2 Embedding Properties**

| Property    | Data Type  | Description              | Configuration                 |
| ----------- | ---------- | ------------------------ | ----------------------------- |
| `embedding` | `number[]` | Content embedding vector | HNSW indexed, cosine distance |

- **embedding**: Stores the numeric vector derived from `content_body`, enabling **semantic similarity** queries via cosine distance.

### **3.3 Metadata Properties**

| Property         | Data Type  | Description               |
| ---------------- | ---------- | ------------------------- |
| `schema_version` | `int`      | Schema version number     |
| `timestamp_utc`  | `date`     | Document timestamp        |
| `parent_id`      | `string`   | Parent document reference |
| `chunk_ids`      | `string[]` | Child chunk references    |

- **schema_version**: Facilitates schema version management.
- **timestamp_utc**: Records when the document was created or updated.
- **parent_id**: Points to a parent document.
- **chunk_ids**: Lists all child chunks, allowing hierarchical document structures.

---

## **4. Index Configurations**

### **4.1 Vector Index (HNSW)**

```json
"vectorIndexConfig": {
  "distance": "cosine",
  "maxConnections": 32,
  "efConstruction": 128,
  "ef": -1,
  "dynamicEfMin": 100,
  "dynamicEfMax": 500,
  "dynamicEfFactor": 8,
  "vectorCacheMaxObjects": 1000000,
  "flatSearchCutoff": 40000
}
```

- **distance:** Uses cosine distance for measuring vector similarity.
- **maxConnections:** Controls node connections in the HNSW graph.
- **efConstruction:** Balances index build speed vs. quality.
- **ef / dynamicEfMin / dynamicEfMax / dynamicEfFactor:** Provide adaptive search depth for queries.
- **vectorCacheMaxObjects:** Limits how many embeddings are cached for faster searches.
- **flatSearchCutoff:** Triggers a flat search for smaller datasets, which can be faster at lower scales.

### **4.2 Text Index (BM25)**

```json
"invertedIndexConfig": {
  "bm25": {
    "b": 0.75,
    "k1": 1.2
  },
  "stopwords": {
    "preset": "en"
  }
}
```

- **BM25 Parameters (`b` and `k1`):** Adjusts weighting for keyword-based search.
- **stopwords:** Uses English stopwords to filter out common words with minimal semantic value.

_Integration Note: Both reports mention HNSW and BM25 configurations—here, we unify them in one section to avoid duplication._

---

## **5. Technical Implementation and Usage**

### **5.1 Vectorization Strategy**

1. **Model Selection:** The `sentence-transformers-all-MiniLM-L6-v2` model generates **384-dimensional** embeddings, suitable for general-purpose document search.
2. **Pooling Strategy:** `mean` pooling ensures each token contributes to the final document vector.
3. **Tokenization Limits:** Each text is truncated to 512 tokens to respect model constraints.

### **5.2 Search Optimization**

- **HNSW Graph Parameters:** Tuning `maxConnections` and `efConstruction` helps balance indexing cost and query speed.
- **Hybrid Search:** By using **BM25** for keyword relevance and **cosine** distance for semantic similarity, you can combine the best of both worlds.
- **Stopword Handling:** The English `stopwords` preset refines text queries, ignoring words like “the,” “a,” or “in.”

_Integration Note: We combined the strategies from both reports. Report A focused on dynamic EF parameters, while Report B provided simpler explanations. We include both here._

### **5.3 Document Relationships**

Documents maintain **hierarchical** structures with parent and child references:

- **Parent-Child Relationship:** `parent_id` for referencing the parent, and `chunk_ids` for listing child chunks.
- **Version Tracking:** `timestamp_utc` and `schema_version` help manage multiple document versions over time.

---

## **6. Practical Examples**

### **6.1 Document Indexing Example**

```python
doc = {
    "content_body": "Main document text...",
    "content_summary": "Brief summary...",
    "content_title": "Document Title",
    "schema_version": 1,
    "timestamp_utc": "2024-01-20T12:00:00Z",
    "parent_id": "parent_doc_123",
    "chunk_ids": ["chunk_1", "chunk_2"]
}
client.data_object.create(doc, "Document")
```

**Analogy:** _Think of the `parent_id` as the “folder” this document belongs to, and `chunk_ids` are smaller files inside that folder._

_Integration Note: Borrowed the code sample from both reports (virtually identical) but added a mini-analogy to illustrate parent-child relationships more clearly._

### **6.2 Semantic Search Example**

```python
response = (
    client.query
    .get("Document")
    .with_near_text({
        "concepts": ["search query"],
        "certainty": 0.7
    })
    .with_additional(["distance"])
    .with_limit(5)
    .do()
)
```

- **Concepts:** The semantic meaning or topic you’re searching for.
- **Certainty:** A confidence threshold for how closely results should match your query.

### **6.3 Relationship Query Example**

```python
# Get all chunks of a parent document
response = (
    client.query
    .get("Document")
    .with_where({
        "path": ["parent_id"],
        "operator": "Equal",
        "valueString": "parent_doc_123"
    })
    .do()
)
```

- **Usage:** Quickly retrieve all child chunks belonging to a single parent.

---

## **7. Schema Management**

### **7.1 Version Control**

- **Schema Versioning:** Use `schema_version` to track changes in structure or indexing strategies.
- **Automated Migration Handling:** Streamline updates by writing migration scripts that transform data into the new format.
- **Backward Compatibility:** Keep older consumers functional while gradually transitioning to newer schema versions.

### **7.2 Data Validation**

- **Property Types:** Ensure each field matches its declared type (text, int, etc.).
- **Required Fields:** Enforce presence of critical fields like `content_body`.
- **Relationship Checks:** Confirm that `parent_id` and `chunk_ids` reference valid documents.

### **7.3 Performance Monitoring**

- **Vector Cache:** Monitor memory usage via `vectorCacheMaxObjects`.
- **Index Cleanup:** Periodically rebuild or compact indexes to maintain performance.
- **Dynamic Parameter Tuning:** Adjust search parameters like `ef` or `b`/`k1` based on workload metrics.

_Integration Note: Report A contributed detailed performance metrics, while Report B clarified the purpose of each. We unify that here._

---

## **8. Best Practices**

1. **Document Chunking**

   - **Respect Token Limits:** Keep each chunk ≤ 512 tokens for full embedding.
   - **Semantic Coherence:** Ensure each chunk covers a single topic or section.
   - **Hierarchical Structure:** Use `parent_id` and `chunk_ids` to link chunks and parent documents.

2. **Vector Search Optimization**

   - **Tune `ef` Values:** Increase for more accurate searches; decrease for faster queries.
   - **Monitor Cache Usage:** Adjust `vectorCacheMaxObjects` to balance speed and memory.
   - **Hybrid Search:** Combine vector and keyword search for optimal results.

3. **Data Management**
   - **Regular Index Maintenance:** Schedule periodic index rebuilds.
   - **Monitor Schema Versions:** Maintain a clear upgrade path.
   - **Validate Relationships:** Prevent orphaned children or broken references.

---

## **9. Optimization Tips and Suggestions**

### **9.1 Resource Planning**

- **Memory Consumption:** Plan for enough memory to handle the HNSW graph size and vector caching.
- **Index Construction Time vs. Query Speed:** A higher `efConstruction` can slow builds but speed up searches.

### **9.2 Future Schema Improvements**

- **Index Additional Properties:** Consider indexing `content_title` or `content_summary` for better keyword search.
- **Metadata Enrichment:** Add properties like `author`, `tags`, or `categories` for advanced queries.
- **Enhanced Relationship Modeling:** Explore cross-links, references, or many-to-many relationships for complex content structures.

_Integration Note: Suggestions from both reports have been consolidated, covering future directions like adding metadata fields or advanced relationship types._

### **9. Schema Architecture and Integration**

### **9.1 Dual Schema Systems**

The project maintains two complementary schema systems:

1. **Core Schema System** (`src/indexing/schema/`)

   - Manages database-level schema definition
   - Handles schema validation and migration
   - Defines core properties and indexes
   - Version control for schema evolution

2. **Document Processing Schema** (`src/connectors/direct_documentation_indexing/`)
   - Handles document-type specific processing
   - Manages source-specific properties
   - Tracks document lineage and transformations
   - Configurable per document type

### **9.2 Integration Points**

The two systems work together through well-defined integration points:

```python
# 1. Base Schema Definition
base_schema = SchemaDefinition.get_schema()  # Core schema

# 2. Source-Specific Schema
doc_tracker = SourceTracker("word")
doc_schema = doc_tracker.get_schema()  # Extends base schema

# 3. Validation
SchemaValidator.validate(doc_schema)  # Validates against core rules
```

### **9.3 Schema Hierarchy**

The schema follows a hierarchical structure:

1. **Base Schema** (Core)

   - Essential properties (`content_body`, `embedding`, etc.)
   - Index configurations
   - Version control

2. **Source-Specific Extensions**

   - Custom properties per document type
   - Processing configurations
   - Type-specific validations

3. **Document Instance**
   - Concrete document data
   - Lineage information
   - Transformation history

### **9.4 Benefits of Separation**

1. **Clear Responsibilities**

   - Core schema: Database structure and search optimization
   - Document schema: Processing and type-specific features

2. **Flexibility**

   - Add new document types without changing core schema
   - Evolve core schema without breaking processors
   - Configure processors independently

3. **Maintainability**
   - Isolated testing of each system
   - Independent versioning
   - Clear upgrade paths

### **9.5 Implementation Example**

```python
# Document Processing Pipeline
class DocumentProcessor:
    def __init__(self, doc_type: str):
        # Initialize both schema systems
        self.source_tracker = SourceTracker(doc_type)
        self.base_schema = SchemaDefinition.get_schema()

    def process_document(self, file_path: Path) -> Dict[str, Any]:
        # 1. Process with type-specific processor
        processor = self.get_processor()
        processed_doc = processor.process(file_path)

        # 2. Get combined schema
        schema = self.source_tracker.get_schema()

        # 3. Transform to schema format
        doc_data = {
            "content_body": processed_doc["content"]["full_text"],
            "schema_version": schema["version"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            # Add source-specific properties
            **{k: v for k, v in processed_doc["metadata"].items()
               if k in schema["properties"]}
        }

        # 4. Validate
        SchemaValidator.validate_object(doc_data, schema)

        return doc_data
```

### **9.6 Future Considerations**

1. **Schema Evolution**

   - Coordinate version changes between systems
   - Maintain backward compatibility
   - Automated migration tools

2. **New Document Types**

   - Template for adding processors
   - Standard property mappings
   - Validation rules

3. **Performance Optimization**
   - Caching strategies
   - Batch processing
   - Parallel validation

---

## **10. Conclusion and Key Takeaways**

1. **Efficient Vector Search**: Leveraging HNSW indexing with cosine distance yields fast, accurate semantic queries.
2. **Hierarchical Document Structure**: Parent-child relationships help manage document versions and sections.
3. **Comprehensive Metadata**: Properties like `timestamp_utc`, `schema_version`, and references offer robust management and version control.
4. **Hybrid Search Capabilities**: Combining BM25 with vector search captures both keywords and semantic meaning.

**Actionable Recommendations:**

- **Regularly Monitor Index Parameters** (e.g., `ef`, `maxConnections`) to optimize performance.
- **Implement Maintenance Routines** for cleaning, reindexing, and verifying relationships.
- **Carefully Plan Document Chunks** to stay within token limits and maintain semantic clarity.

_Integration Note: We included the bullet-style summary from Report A but added the user-friendly recommendations format from Report B._

---

## **11. Current Implementation Details**

The schema is implemented through a robust, multi-layered architecture that provides comprehensive schema management, validation, and migration capabilities.

### **11.1 Core Components**

1. **SchemaManager (Facade)**

   - Provides a simplified interface for schema operations
   - Maintains backward compatibility
   - Handles schema migrations
   - Manages resource cleanup and error recovery

2. **SchemaMigrator**

   - Creates new schemas when they don't exist
   - Validates existing schemas against current definitions
   - Migrates schemas to newer versions
   - Provides detailed logging of all operations

3. **SchemaValidator**

   - Retrieves and inspects existing schemas
   - Validates schema configurations against requirements
   - Checks schema versions for compatibility
   - Ensures all required properties are present and correctly typed

4. **SchemaDefinition**
   - Defines the complete schema structure
   - Configures vector embeddings using text2vec-transformers
   - Sets up BM25 text indexing with customized parameters
   - Configures HNSW vector index for fast similarity search

### **11.2 Advanced Features**

1. **Vector Search Configuration**

   ```json
   "vectorIndexConfig": {
       "skip": false,
       "maxConnections": 32,
       "efConstruction": 128,
       "ef": -1,
       "dynamicEfMin": 100,
       "dynamicEfMax": 500,
       "dynamicEfFactor": 8,
       "vectorCacheMaxObjects": 1000000,
       "flatSearchCutoff": 40000,
       "distance": "cosine"
   }
   ```

2. **Text Search Optimization**

   ```json
   "invertedIndexConfig": {
       "bm25": {
           "b": 0.75,
           "k1": 1.2
       },
       "stopwords": {
           "preset": "en"
       }
   }
   ```

3. **Comprehensive Property Validation**
   - Content properties (body, title, summary)
   - Embedding properties with vector configurations
   - Metadata properties (timestamp, version)
   - Relationship properties (parent-child structure)

### **11.3 Migration and Version Control**

The system provides a complete migration path for schema updates:

1. Version tracking through `SchemaDefinition.SCHEMA_VERSION`
2. Automatic schema validation before migrations
3. Safe migration process with proper error handling
4. Comprehensive logging of all migration steps

### **11.4 Future Enhancements**

Potential areas for enhancement include:

1. Additional metadata fields:
   - Categories for improved document classification
   - Platform-specific metadata for source tracking
2. Enhanced relationship modeling for complex document structures
3. Advanced caching strategies for improved performance

_Note: The current implementation exceeds the basic recommendations in this document, providing a more robust and feature-complete solution for schema management._
