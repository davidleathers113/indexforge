# Schema Mismatch Test Documentation

## Purpose

Validates the system's handling of schema mismatches and incompatibilities.

## Test Cases and Expected Outcomes

### 1. Field Definition Mismatch

- **Description**: Tests handling of mismatched field definitions
- **Test Cases**:
  - Unknown fields
  - Custom fields
- **Expected Outcome**:
  - ValueError with "unknown.\*field" message
- **Implementation Notes**:
  - Field validation
  - Schema comparison
  - Error handling

### 2. Field Type Mismatch

- **Description**: Tests handling of mismatched field types
- **Test Cases**:
  - content_body as number
  - schema_version as string
  - chunk_ids as string
  - embedding as string
- **Expected Outcome**:
  - TypeError with "{field}.\*type" message
- **Implementation Notes**:
  - Type checking
  - Validation rules
  - Error messaging

### 3. Metadata Schema Mismatch

- **Description**: Tests handling of mismatched metadata schemas
- **Test Cases**:
  - List instead of dict
  - Number instead of dict
  - String instead of dict
  - Too deeply nested
- **Expected Outcome**:
  - TypeError or ValueError
- **Implementation Notes**:
  - Structure validation
  - Nesting checks
  - Type verification

### 4. Embedding Dimension Mismatch

- **Description**: Tests handling of mismatched embedding dimensions
- **Test Cases**:
  - Too few dimensions (128)
  - Too many dimensions (512)
  - Empty embedding
  - Single dimension
- **Expected Outcome**:
  - ValueError with "embedding.\*dimension" message
- **Implementation Notes**:
  - Dimension validation
  - Size checking
  - Format verification

### 5. Processor Schema Mismatch

- **Description**: Tests handling of mismatches between processor and core schema
- **Test Cases**:
  - Processor-specific fields
  - Unsupported source type
- **Expected Outcome**:
  - ValueError with "processor.\*schema" message
- **Implementation Notes**:
  - Schema mapping
  - Field compatibility
  - Error handling

### 6. Relationship Schema Mismatch

- **Description**: Tests handling of mismatched relationship schemas
- **Test Cases**:
  - parent_id as list
  - chunk_ids as string
  - parent_id as dict
  - Mixed types in chunk_ids
- **Expected Outcome**:
  - TypeError or ValueError
- **Implementation Notes**:
  - Reference validation
  - Type checking
  - Format verification

### 7. Timestamp Format Mismatch

- **Description**: Tests handling of mismatched timestamp formats
- **Test Cases**:
  - Missing time
  - Missing date
  - Wrong format
  - Invalid values
  - Number instead of string
- **Expected Outcome**:
  - ValueError with "timestamp.\*format" message
- **Implementation Notes**:
  - Format validation
  - Value checking
  - Type verification

### 8. Content Format Mismatch

- **Description**: Tests handling of mismatched content formats
- **Test Cases**:
  - Binary data
  - List content
  - Dict content
  - Number content
  - Boolean content
- **Expected Outcome**:
  - TypeError with "content.\*string" message
- **Implementation Notes**:
  - Content validation
  - Type checking
  - Format verification

## Risk Assessment

- **Criticality**: HIGH
- **Impact of Failure**:
  - Data corruption
  - Processing errors
  - Invalid schemas
  - System instability
  - Data inconsistency

## Coverage Gaps

- Complex type validation
- Custom field mapping
- Schema versioning
- Migration handling
- Error recovery

## Test Dependencies

- Requires SchemaValidator
- Uses text_processing utils
- Needs base_schema fixture
- Depends on generate_embeddings
