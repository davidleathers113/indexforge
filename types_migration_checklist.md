# Types Migration Checklist

## 1. Initial Setup

### Directory Structure

- [x] Create core types directory structure:

```
src/core/types/
├── __init__.py
├── service/
│   ├── __init__.py
│   ├── states.py        # ServiceState, lifecycle states
│   ├── protocols.py     # AsyncContextManager, base protocols
│   └── errors.py        # Service-related errors
├── storage/
│   ├── __init__.py
│   ├── metrics.py       # StorageMetrics protocol
│   ├── strategies.py    # StorageStrategy protocols
│   └── errors.py        # Storage-related errors
├── processing/
│   ├── __init__.py
│   ├── validation.py    # ValidationStrategy protocols
│   ├── states.py        # ProcessingStatus, states
│   └── operations.py    # TransformationType, operations
└── security/
    ├── __init__.py
    ├── keys.py          # KeyType, key-related types
    ├── common.py        # Shared security types
    └── errors.py        # Security error hierarchy
```

## 2. Service Types Migration

### Core Service Types

- [x] Move ServiceState enum from `src/core/base.py`
- [x] Move AsyncContextManager protocol
- [x] Extract service error types

### Import Updates

- [x] Update imports in dependent files
  - [x] src/core/security/provider.py
  - [x] tests/unit/core/security/test_provider.py
  - [x] src/core/document/operations.py
  - [x] tests/core/document/test_operations.py
- [x] Add type exports in `service/__init__.py`
- [x] Verify no circular imports

## 3. Storage Types Migration

### Core Storage Types

- [x] Move StorageMetrics protocol from `src/core/interfaces/storage.py`
- [x] Move StorageStrategy protocol
- [x] Extract storage error types

### Implementation Updates

- [x] Update repository base types
- [x] Add type exports in `storage/__init__.py`
- [x] Update storage implementation imports
  - [x] src/services/storage/**init**.py
  - [x] src/services/storage/base.py
  - [x] src/services/storage/metrics.py
  - [x] src/services/storage/document_storage.py
  - [x] src/services/storage/chunk_storage.py
  - [x] src/services/storage/reference_storage.py
  - [x] src/core/storage/repositories/documents.py
  - [x] src/core/storage/repositories/lineage.py
  - [x] src/core/storage/strategies/memory_storage/exceptions.py
  - [x] tests/core/storage/strategies/test_performance.py
  - [x] tests/core/storage/strategies/test_memory_storage.py

## 4. Processing Types Migration

### Core Processing Types

- [x] Move ValidationStrategy from `src/core/interfaces/processing.py`
- [x] Move ProcessingStatus from `src/core/tracking/enums.py`
- [x] Move TransformationType
- [x] Extract processing error types

### Implementation Updates

- [x] Add type exports in `processing/__init__.py`
- [x] Update processor implementations
  - [x] src/ml/processing/base.py (has linter errors to fix)
  - [x] src/ml/processing/text.py
  - [x] src/ml/processing/validation/chunk_validator.py
  - [x] src/ml/processing/models/strategies.py
  - [x] src/ml/processing/models/converters.py
  - [x] src/ml/processing/models/chunks.py

## 5. Security Types Migration

### Core Security Types

- [x] Move KeyType enum from `src/core/security/common.py`
- [x] Move security error hierarchy
- [x] Move key-related type definitions
- [x] Extract shared security types

### Implementation Updates

- [x] Add type exports in `security/__init__.py`
- [x] Update security service imports
  - [x] src/core/security/provider.py
  - [x] src/core/security/encryption.py
  - [x] src/core/security/key_storage.py
  - [ ] tests/core/security/test_provider.py
  - [ ] tests/core/security/test_encryption.py
  - [ ] tests/core/security/test_key_storage.py

## 6. Type Validation and Testing

### Type System

- [ ] Add type hints to all new modules
- [ ] Verify type consistency
- [ ] Add docstrings for all types
- [ ] Run mypy type checking
- [ ] Update affected tests

## 7. Import Updates

### Global Import Cleanup

- [ ] Update all imports in core modules
- [ ] Update imports in ML services
- [ ] Update imports in API layer
- [ ] Verify import order
- [ ] Remove unused imports

## 8. Documentation

### Documentation Updates

- [ ] Add module docstrings
- [ ] Document type hierarchies
- [ ] Update API documentation
- [ ] Add migration notes
- [ ] Update type usage examples

## 9. Testing Strategy

### Test Coverage

- [ ] Unit tests for type validation
- [ ] Integration tests for type usage
- [ ] Test circular import prevention
- [ ] Test type compatibility
- [ ] Verify test coverage

## 10. Cleanup and Verification

### Final Verification

- [ ] Remove duplicate type definitions
- [ ] Verify no remaining circular imports
- [ ] Check for unused types
- [ ] Validate type consistency
- [ ] Update type exports

## 11. Performance Considerations

### Performance Optimization

- [ ] Minimize import overhead
- [ ] Optimize type checking
- [ ] Profile type usage
- [ ] Document performance impacts

## 12. Migration Steps

### Implementation Order

- [x] Create new type modules
- [x] Move types in dependency order
- [🔄] Update imports incrementally
- [🔄] Run tests after each move
- [ ] Document breaking changes

## Notes

- Add specific details and dependencies as they are discovered
- Mark completion dates for each item
- Document any issues or blockers
- Track performance metrics throughout
- Note any required rollbacks

## Dependencies

### Key Files to Monitor

- `src/core/base.py`
- `src/core/interfaces/`
- `src/core/models/`
- `src/core/security/`
- `src/core/tracking/`
- `src/ml/` (for import updates)
- `tests/` (for test updates)

### Critical Paths

1. Service types (most dependencies)
2. Storage types (used by services)
3. Processing types (used by ML)
4. Security types (relatively independent)

## Success Criteria

- [🔄] All types properly organized in `core/types`
- [🔄] No circular imports
- [🔄] All tests passing
- [🔄] Type checking clean
- [🔄] Documentation updated
- [🔄] No duplicate type definitions
- [🔄] Clear import paths
- [🔄] Maintained backward compatibility
- [🔄] Performance metrics within targets

## Current Status

### Completed

- Processing types migration is complete except for linter errors in base.py
- All processor implementations have been updated to use new types
- No new circular dependencies introduced

### In Progress

- Fixing linter errors in src/ml/processing/base.py
- Moving on to security types migration next

### Blockers

- Need to resolve linter errors in base.py related to ProcessingStateError constructor calls
