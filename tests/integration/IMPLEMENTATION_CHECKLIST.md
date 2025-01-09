# Schema Integration Implementation Checklist (TDD Approach)

## Table of Contents

1. [Test-First Development Process](#test-first-development-process)
2. [Existing Test Files](#existing-test-files-your-specifications)
3. [Schema Validation Framework](#1-schema-validation-framework)
4. [Document Relationship Validation](#2-document-relationship-validation)
5. [Text Processing and Embeddings](#3-text-processing-and-embeddings)
6. [Hybrid Search Implementation](#4-hybrid-search-implementation)
7. [Document Processing](#5-document-processing)
8. [Property Mapping](#6-property-mapping)
9. [Schema Version Management](#7-schema-version-management)
10. [Development Guidelines](#development-guidelines)
11. [File Naming Conventions](#file-naming-conventions)
12. [Implementation Order](#implementation-order-tdd-cycles)
    - [TDD Workflow](#tdd-workflow-for-each-component)
    - [Dependency Graph](#dependency-graph)
    - [Implementation Phases](#implementation-phases)
13. [Testing Requirements](#testing-requirements)
14. [Test Dependencies and Setup](#test-dependencies-and-setup)

> **IMPORTANT NOTE**: This is a Test-Driven Development (TDD) project. All test files have already been created in the `tests/integration` directory and serve as our specifications. Our task is to implement the functionality by following the TDD cycle:
>
> 1. **RED**: Run the existing tests (they will fail)
> 2. **GREEN**: Implement the minimum code needed to make the tests pass
> 3. **REFACTOR**: Clean up the code while keeping tests green
>
> DO NOT create new test files. Instead, use the existing tests to guide your implementation.

## Test-First Development Process

1. Start with the test file for the feature you're implementing
2. Run the test to see it fail and understand the expected behavior
3. Implement the minimum code needed to make the test pass
4. Run all related tests to ensure no regressions
5. Refactor while keeping tests green
6. Move to the next test in the dependency order

## Existing Test Files (Your Specifications)

All test files are already implemented in these locations:

- Edge Cases: `tests/integration/edge_cases/`
  - Use for implementing boundary conditions and error cases
- Error Handling: `tests/integration/error_handling/`
  - Use for implementing validation and error responses
- Performance: `tests/integration/performance/`
  - Use for implementing performance requirements
- Property Mapping: `tests/integration/property_mapping/`
  - Use for implementing metadata mapping
- Search: `tests/integration/search/`
  - Use for implementing search functionality
- Validation: `tests/integration/validation/`
  - Use for implementing core validation logic
- Versioning: `tests/integration/versioning/`
  - Use for implementing schema versioning

Each test file contains examples and assertions that specify exactly how the feature should behave. Use these as your requirements.

## 1. Schema Validation Framework

### SchemaValidator Implementation

```python
class SchemaValidator:
    @staticmethod
    def validate_object(doc: Dict[str, Any]) -> None:
        # Implementation needed
        pass
```

### Required Field Validation

- [ ] Missing fields raise ValueError with "{field}.\*required"
- [ ] None values raise ValueError
- [ ] Empty string values raise ValueError with "{field}.\*empty"
- [ ] Fields to validate:
  - content_body
  - timestamp_utc (ISO format)
  - schema_version (positive integer)
  - embedding (384-dim numeric list)

### Type Validation

- [ ] Wrong types raise TypeError with "{field}.\*{expected_type}"
- [ ] Schema version must be integer
- [ ] Embedding must be list of numbers
- [ ] Timestamp must be ISO format string

### Size Constraints

- [ ] Content body: 100KB limit
- [ ] Chunk list: 1000 chunks max
- [ ] Embedding: exactly 384 dimensions
- [ ] Metadata: 100 levels deep max
- [ ] Metadata fields: 100 fields max

### Metadata Validation

- [ ] Metadata structure validation (must be dict)
- [ ] Nesting depth validation (max 100 levels)
- [ ] Field count validation (max 100 fields)
- [ ] Type validation for metadata values
- [ ] Custom field validation rules

## 2. Document Relationship Validation

### Relationship Validator Implementation

```python
def validate_relationships(doc: Dict[str, Any], doc_store: DocumentStore) -> None:
    # Implementation needed
    pass
```

### Circular Reference Detection

- [ ] Direct self-reference (A → A)
- [ ] Indirect circular reference (A → B → A)
- [ ] Complex circular chain (A → B → C → A)
- [ ] Mixed parent-child circular references
- [ ] Self-reference in chunk_ids

### Valid Relationship Validation

- [ ] Valid parent-child relationships
- [ ] Valid chunk references
- [ ] Complex but valid hierarchies

### Concurrency Handling

- [ ] Concurrent document updates
- [ ] Lock management for relationships
- [ ] Race condition prevention
- [ ] Deadlock detection and prevention

## 3. Text Processing and Embeddings

### Embedding Generator Implementation

```python
def generate_embeddings(text: str) -> np.ndarray:
    # Implementation needed
    pass
```

### Embedding Features

- [ ] Generate 384-dimensional vectors
- [ ] Consistent output for same input
- [ ] Handle empty/invalid input
- [ ] Numeric value constraints

### Language Support

- [ ] Cross-language query handling
- [ ] Language detection
- [ ] Translation handling
- [ ] Multi-language result ranking
- [ ] Language-specific tokenization

## 4. Hybrid Search Implementation

### Search Engine Implementation

```python
class SchemaDefinition:
    def search(self, query: str, documents: List[Dict], hybrid_alpha: float = 0.5) -> List[Dict]:
        # Implementation needed
        pass
```

### BM25 Implementation

- [ ] Exact keyword matching
- [ ] Term frequency weighting
- [ ] Document length normalization

### Vector Similarity

- [ ] Semantic similarity matching
- [ ] Embedding comparison
- [ ] Distance calculation

### Hybrid Search Features

- [ ] Weight balancing (hybrid_alpha)
- [ ] Result ranking
- [ ] Out-of-vocabulary handling

### Performance Requirements

- [ ] Memory usage < 10MB per 1000 docs
- [ ] Query response time < 1 second
- [ ] Cache hit rate > 80%
- [ ] Linear scaling with document count
- [ ] Resource cleanup verification
- [ ] Connection pooling optimization

## 5. Document Processing

### Base Processor Implementation

```python
class BaseProcessor:
    def process(self, content: Any) -> Dict[str, Any]:
        # Implementation needed
        pass
```

### Size Validation

- [ ] Content body size limits
- [ ] Chunk list size limits
- [ ] Metadata depth limits
- [ ] Field count limits

### Content Processing

- [ ] UTF-8 encoding
- [ ] Special character handling
- [ ] Binary content rejection
- [ ] Format validation

### Error Recovery

- [ ] Transaction rollback support
- [ ] Partial update handling
- [ ] Validation chain recovery
- [ ] Resource cleanup on failure
- [ ] Error state logging
- [ ] Recovery procedure documentation

## 6. Property Mapping

### Property Mapper Implementation

```python
class PropertyMapper:
    def map_source_metadata(self, source_doc: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation needed
        pass
```

### Mapping Features

- [ ] Basic metadata mapping
- [ ] Custom field mapping
- [ ] Array field preservation
- [ ] Nested structure mapping

## 7. Schema Version Management

### Version Migration

- [ ] Version migration paths (v1 → latest)
- [ ] Backward compatibility handling
- [ ] Field deprecation warnings
- [ ] Rollback scenarios
- [ ] Concurrent migration handling

### Migration Features

- [ ] Field renaming support
- [ ] Type conversion handling
- [ ] Default value injection
- [ ] Schema validation per version
- [ ] Migration state tracking

### Concurrent Operations

- [ ] Parallel migration support
- [ ] Resource contention handling
- [ ] Lock management
- [ ] Progress tracking
- [ ] Failure recovery

## Development Guidelines

### Test Structure Pattern

```python
def test_feature_name(fixture1, fixture2):
    """Test description."""
    # Arrange
    doc = deepcopy(fixture1)

    # Act
    result = function_under_test(doc)

    # Assert
    assert condition
```

### Required Fixtures (from conftest.py)

- [ ] base_schema
- [ ] doc_tracker
- [ ] valid_document
- [ ] mock_processor

### Error Handling Pattern

```python
with pytest.raises(ValueError, match="expected.*pattern"):
    SchemaValidator.validate_object(invalid_doc)
```

### Helper Functions

```python
def create_test_document(**overrides) -> Dict[str, Any]:
    doc = deepcopy(valid_document)
    doc.update(overrides)
    return doc
```

## File Naming Conventions

When implementing components, use descriptive and specific names that clearly indicate the file's purpose. Follow these patterns:

### Core Components

- `schema_validator.py` instead of `schema.py`
- `document_relationship_validator.py` instead of `validator.py`
- `embedding_generator.py` instead of `embeddings.py`
- `schema_version_migrator.py` instead of `migration.py`

### Processing Components

- `word_document_processor.py` instead of `processor.py`
- `pdf_document_processor.py` instead of `pdf.py`
- `metadata_field_mapper.py` instead of `mapper.py`
- `document_content_extractor.py` instead of `extractor.py`

### Search Components

- `hybrid_search_engine.py` instead of `search.py`
- `bm25_text_ranker.py` instead of `ranker.py`
- `vector_similarity_calculator.py` instead of `similarity.py`
- `search_result_aggregator.py` instead of `results.py`

### Validation Components

- `field_type_validator.py` instead of `types.py`
- `size_constraint_validator.py` instead of `size.py`
- `relationship_cycle_detector.py` instead of `detector.py`
- `metadata_structure_validator.py` instead of `metadata.py`

### Naming Rules

1. Use full words, not abbreviations (e.g., `document` not `doc`)
2. Include the component type in the name (e.g., `validator`, `processor`, `calculator`)
3. Be specific about the functionality (e.g., `relationship_cycle_detector` not `cycle_checker`)
4. Use nouns for classes/modules and verbs for functions
5. Follow Python's snake_case convention
6. Group related functionality with common prefixes
7. Indicate the primary domain in the name (e.g., `schema_`, `document_`, `search_`)

### Directory Structure

```
src/
├── schema/
│   ├── validation/
│   │   ├── field_type_validator.py
│   │   ├── size_constraint_validator.py
│   │   └── metadata_structure_validator.py
│   ├── processing/
│   │   ├── document_content_extractor.py
│   │   └── metadata_field_mapper.py
│   └── search/
│       ├── hybrid_search_engine.py
│       └── vector_similarity_calculator.py
```

### Examples of Bad vs Good Names

❌ Bad:

- `schema.py` (too generic)
- `processor.py` (unclear purpose)
- `utils.py` (too vague)
- `helper.py` (non-descriptive)
- `manager.py` (ambiguous)

✅ Good:

- `schema_field_validator.py` (specific purpose)
- `word_document_processor.py` (clear scope)
- `embedding_distance_calculator.py` (explicit functionality)
- `document_relationship_validator.py` (clear domain)
- `search_result_ranker.py` (specific role)

## Implementation Order (TDD Cycles)

Each component should follow the RED → GREEN → REFACTOR cycle:

1. **Core Schema Validation** (Base Requirement)

   - Start with `test_validate_required_fields.py`
   - Run tests to see failures (RED)
   - Implement SchemaValidator to pass tests (GREEN)
   - Refactor while maintaining passing tests
   - _Required by: All other components_

2. **Text Processing and Embeddings** (Independent Core Feature)

   - Start with basic text processing tests
   - Implement minimum code to pass (GREEN)
   - Add embedding functionality incrementally
   - Refactor for performance
   - _Required by: Hybrid Search, Document Processing_

3. **Document Processing** (Depends on: 1, 2)

   - Begin with basic processing tests
   - Implement BaseProcessor incrementally
   - Add validation and error handling
   - Refactor for robustness
   - _Required by: Property Mapping_

4. **Property Mapping** (Depends on: 1, 3)

   - Start with `test_custom_property_mapping.py`
   - Implement mapping logic incrementally
   - Add custom field handling
   - Refactor for maintainability
   - _Required by: Document Relationships_

5. **Document Relationship Validation** (Depends on: 1, 4)

   - Begin with `test_circular_references.py`
   - Implement relationship validation
   - Add concurrency handling
   - Refactor for efficiency
   - _Required by: Schema Version Management_

6. **Schema Version Management** (Depends on: 1, 4, 5)

   - Start with version migration tests
   - Implement migration logic
   - Add concurrent operations
   - Refactor for reliability
   - _Required by: Production Deployment_

7. **Hybrid Search Implementation** (Depends on: 1, 2)
   - Begin with `test_hybrid_search.py`
   - Implement search components incrementally
   - Add performance optimizations
   - Refactor for scalability
   - _Independent feature but requires core components_

### TDD Workflow for Each Component

```
1. Run relevant test file → RED
   ↓
2. Implement minimum code
   ↓
3. Run tests → GREEN
   ↓
4. Refactor
   ↓
5. Run all dependent tests
   ↓
6. Move to next feature
```

### Dependency Graph

```
1. Core Schema Validation
    ↓
2. Text Processing  →  7. Hybrid Search
    ↓
3. Document Processing
    ↓
4. Property Mapping
    ↓
5. Document Relationships
    ↓
6. Schema Version Management
```

### Implementation Phases

**Phase 1: Core Infrastructure**

1. Basic Schema Validation (Week 1)

   - Set up SchemaValidator class
   - Implement basic field presence checks
   - Add type validation
   - _Test Dependencies: valid_document fixture_
   - _Success Criteria: All basic field validation tests pass_

2. Advanced Schema Validation (Week 1-2)

   - Implement size constraints
   - Add metadata validation
   - Add nested field validation
   - _Test Dependencies: valid_document, base_schema fixtures_
   - _Success Criteria: All size and metadata validation tests pass_

3. Text Processing Foundation (Week 2)

   - Set up text normalization
   - Implement UTF-8 handling
   - Add special character processing
   - _Test Dependencies: valid_document fixture_
   - _Success Criteria: All text processing tests pass_

4. Embedding System (Week 2-3)
   - Implement embedding generation
   - Add dimension validation
   - Set up numeric constraints
   - _Test Dependencies: valid_document, base_schema fixtures_
   - _Success Criteria: All embedding tests pass, performance metrics met_

_Exit Criteria for Phase 1:_

- All core validation tests passing
- Text processing pipeline complete
- Embedding system operational
- Performance benchmarks met
- No critical bugs in validation logic

**Phase 2: Document Handling** (Weeks 3-5)

1. Base Document Processing (Week 3)

   - Set up BaseProcessor class
   - Implement basic content extraction
   - Add format detection
   - _Test Dependencies: valid_document, base_schema fixtures_
   - _Success Criteria: Basic document processing tests pass_

2. Advanced Processing Features (Week 4)

   - Implement UTF-8 handling
   - Add binary content detection
   - Set up special character processing
   - Add error recovery mechanisms
   - _Test Dependencies: valid_document, base_schema, mock_processor fixtures_
   - _Success Criteria: All processing edge case tests pass_

3. Property Mapping Foundation (Week 4)

   - Implement PropertyMapper class
   - Set up basic field mapping
   - Add type conversion handling
   - _Test Dependencies: valid_document, mock_processor fixtures_
   - _Success Criteria: Basic mapping tests pass_

4. Advanced Property Mapping (Week 5)
   - Add nested structure mapping
   - Implement array field handling
   - Set up custom field mapping
   - Add validation chains
   - _Test Dependencies: All Phase 2 fixtures_
   - _Success Criteria: All property mapping tests pass_

_Exit Criteria for Phase 2:_

- All document processing tests passing
- Property mapping fully functional
- Error recovery mechanisms verified
- Performance requirements met
- Integration tests with Phase 1 passing

**Phase 3: Relationships and Versioning** (Weeks 5-7)

1. Basic Relationship Management (Week 5)

   - Implement relationship validator
   - Set up basic parent-child validation
   - Add UUID validation
   - _Test Dependencies: Phase 1 & 2 fixtures_
   - _Success Criteria: Basic relationship tests pass_

2. Advanced Relationship Features (Week 6)

   - Add circular reference detection
   - Implement relationship graph traversal
   - Set up concurrent update handling
   - Add deadlock prevention
   - _Test Dependencies: All previous fixtures_
   - _Success Criteria: All relationship edge case tests pass_

3. Version Management Setup (Week 6)

   - Implement version tracking
   - Set up migration framework
   - Add backward compatibility checks
   - _Test Dependencies: All previous fixtures_
   - _Success Criteria: Basic version management tests pass_

4. Advanced Version Features (Week 7)
   - Add concurrent migration handling
   - Implement rollback mechanisms
   - Set up state tracking
   - Add progress monitoring
   - _Test Dependencies: All fixtures_
   - _Success Criteria: All version management tests pass_

_Exit Criteria for Phase 3:_

- All relationship tests passing
- Version migration framework operational
- Concurrency handling verified
- No data corruption in migrations
- All integration tests passing

**Phase 4: Search Capabilities** (Weeks 7-9)

1. Search Infrastructure (Week 7)

   - Set up search engine class
   - Implement basic text search
   - Add result ranking framework
   - _Test Dependencies: Phase 1 fixtures_
   - _Success Criteria: Basic search tests pass_

2. BM25 Implementation (Week 8)

   - Implement term frequency calculation
   - Add inverse document frequency
   - Set up document length normalization
   - Add relevance scoring
   - _Test Dependencies: Search fixtures_
   - _Success Criteria: BM25 accuracy tests pass_

3. Vector Search Features (Week 8)

   - Implement vector similarity
   - Add distance calculations
   - Set up vector indexing
   - Optimize performance
   - _Test Dependencies: Embedding fixtures_
   - _Success Criteria: Vector search accuracy tests pass_

4. Hybrid Search Integration (Week 9)
   - Implement weight balancing
   - Add result merging
   - Set up performance optimization
   - Add caching layer
   - _Test Dependencies: All search fixtures_
   - _Success Criteria: All search tests pass_

_Exit Criteria for Phase 4:_

- All search accuracy tests passing
- Performance requirements met:
  - Query response < 1 second
  - Memory usage < 10MB/1000 docs
  - Cache hit rate > 80%
- Integration tests passing
- Load testing successful

### Overall Project Success Criteria

- All phases completed within 9 weeks
- All test suites passing
- Performance requirements met
- No critical bugs
- Documentation complete
- Integration tests passing
- Load testing successful

### Risk Mitigation

- Weekly code reviews
- Daily test runs
- Performance monitoring
- Regular dependency updates
- Security scanning
- Backup and recovery testing

## Testing Requirements

- Each feature must have corresponding test file
- Tests must cover both success and failure cases
- Use pytest fixtures for common test data
- Follow AAA (Arrange-Act-Assert) pattern
- Include docstrings with test descriptions
- Maintain test independence
- Performance test requirements:
  - Memory usage tests
  - Response time measurements
  - Concurrent operation tests
  - Resource cleanup verification
  - Cache efficiency tests

## Test Dependencies and Setup

### Existing Core Test Files

The following test files are already implemented and will guide your implementation:

- `test_validate_required_fields.py`

  - Use as specification for basic field requirements
  - Must pass before proceeding to other implementations

- `test_schema_mismatch.py`

  - Use as specification for type checking
  - Required before implementing property mapping

- `test_circular_references.py`
  - Use as specification for relationship logic
  - Required before implementing document relationships

### Existing Test Fixtures

The following fixtures are already defined in `conftest.py`:

1. `valid_document`

   - Already implemented
   - Base fixture for all validation tests
   - Required by: All other tests

2. `base_schema`

   - Already implemented
   - Core schema configuration
   - Required by: Validation, search, and processing tests

3. `doc_tracker`

   - Already implemented
   - Document source tracking
   - Required by: Processing and mapping tests

4. `mock_processor`
   - Already implemented
   - Document processing simulation
   - Required by: Processing and mapping tests

### Test Categories Dependencies

```
test_validate_required_fields.py
↓
test_schema_mismatch.py
↓
test_circular_references.py → test_oversized_documents.py
↓
test_custom_property_mapping.py
↓
test_hybrid_search.py
```

### Performance Test Setup

- Memory profiling tools
- Response time measurement framework
- Concurrent operation test framework
- Resource monitoring tools

_Note: Each test category should have its own test data fixtures to ensure test isolation_
