# Dependency Refactoring Implementation Plan

## Progress Update - [2024-03-23]

### Recently Completed ✅

- Moved settings to centralized `src/config/` package
- Added ML package structure with embeddings, processing, and search modules
- Configured Ruff for import sorting and dependency management
- Added missing dependencies (backoff, scikit-learn, langdetect) to poetry groups
- Implemented robust `BaseService` class with core functionality
- Fixed AsyncContextManager implementation using Protocol
- Fixed imports in ML modules
- Standardized core interfaces with Protocol pattern
- Implemented `ChunkProcessor` in ML package
- Added core dependencies and error handling
- Refactored ChunkValidator using design patterns
- Organized ML processing package structure
- Implemented metrics collection system
- Consolidated error definitions
- Initial refactoring of performance analysis module

### Currently In Progress 🚧

#### Completed Components (100%)

- Processing interface standardization
- Core Interface Refinement
- Redis and Weaviate service implementations
- Package structure reorganization
- Interface exports in **init**.py

#### Partially Complete Components

- Embedding interface refinement (70%)

  - Missing: Advanced embedding strategies
  - Missing: Batch processing optimizations
  - Missing: Caching mechanisms
  - Missing: Error recovery strategies

- Cross-referencing interface implementations (85%)

  - Missing: Full validation of cross-references
  - Missing: Circular dependency checks
  - Missing: Performance impact analysis

- Processor interfaces implementation (90%)
  - Missing: Edge case handling
  - Missing: Resource cleanup
  - Missing: Performance optimizations

#### Major Incomplete Components

1. CI Pipeline (60%)

   - Missing:
     - End-to-end test configuration
     - Deployment workflows
     - Environment-specific configs
     - Performance benchmarks
     - Security scanning
     - Artifact management
     - Release automation

2. Integration Tests (75%)

   - Missing:
     - Cross-service integration scenarios
     - Long-running operation tests
     - Load testing
     - System state verification
     - Failure recovery testing
     - Resource leak detection
     - Performance degradation tests

3. End-to-end Tests (60%)

   - Missing:
     - Complete test suite structure
     - User flow testing
     - System integration tests
     - Performance benchmarks
     - Load testing scenarios
     - Error scenario coverage
     - Data consistency validation

4. Circular Dependencies (80%)
   - Missing:
     - Complete dependency graph analysis
     - Runtime import verification
     - Cycle detection in ML package
     - Performance impact assessment
     - Documentation of dependencies

### Implementation Details 📋

1. **Core Interface Refinement** (100% Complete)

   - ✅ Convert all interfaces to Protocol pattern
   - ✅ Implement forward references for model types
   - ✅ Add TYPE_CHECKING imports
   - ✅ Enhance documentation and type hints
   - ✅ Complete storage interfaces
   - ✅ Complete reference interfaces
   - ✅ Implement ChunkProcessor
   - ✅ Implement base processor interfaces
   - ✅ Complete remaining processor interfaces
   - ✅ Verify interface exports

2. **Service Implementation** (90% Complete)

   - ✅ Update base.py with new service patterns
   - ✅ Implement proper error handling and state management
   - ✅ Implement service health checks
   - ✅ Implement Redis service with new interfaces
   - ✅ Implement Weaviate service with new interfaces
   - 🚧 Complete service integration tests (75% complete)

3. **Container Configuration** (85% Complete)
   - ✅ Update dependency injection setup
   - ✅ Add proper error handling for service startup
   - ✅ Implement health checks and monitoring
   - ✅ Configure service initialization order
   - 🚧 Complete container integration tests (60% complete)

### Updated Next Steps ⏳

1. Complete End-to-end Test Suite

   - [ ] Create dedicated e2e test directory
   - [ ] Implement user flow test scenarios
   - [ ] Add system integration tests
   - [ ] Configure test data management
   - [ ] Add performance benchmark suite
   - [ ] Implement load testing framework
   - [ ] Add error scenario coverage
   - [ ] Create data consistency checks

2. Enhance CI Pipeline

   - [ ] Set up end-to-end test runners
   - [ ] Configure deployment workflows
   - [ ] Add environment-specific configs
   - [ ] Implement security scanning
   - [ ] Set up artifact management
   - [ ] Configure release automation
   - [ ] Add performance benchmark tracking

3. Complete Integration Testing

   - [ ] Add cross-service scenarios
   - [ ] Implement long-running tests
   - [ ] Add load testing suite
   - [ ] Create state verification tests
   - [ ] Add failure recovery scenarios
   - [ ] Implement resource monitoring
   - [ ] Add performance regression tests

4. Resolve Dependency Issues
   - [ ] Complete dependency graph analysis
   - [ ] Verify runtime import behavior
   - [ ] Fix ML package cycles
   - [ ] Document dependency structure
   - [ ] Optimize import performance
   - [ ] Add dependency validation tests

### Known Issues 🐛

- Some circular import dependencies remain in ML package (mostly resolved)
- Need to standardize error handling patterns across all interfaces
- Variable type hint coverage in some implementations
- Need to verify backward compatibility with existing clients
- Integration test coverage needs improvement
- Performance testing for large-scale operations needed

## Implementation Plan

### Phase 1: Package Structure Reorganization ✅

- [x] Move settings to centralized package
- [x] Add ML package structure
- [x] Configure Ruff for import sorting
- [x] Implement BaseService class

### Phase 2: Fix Circular Imports (90% Complete)

- [x] Identify all circular dependencies
- [x] Refactor import structure in core modules
- [x] Add proper type hints to core interfaces
- [x] Complete ML package import refactoring
- 🚧 Verify no remaining circular dependencies (80% complete)

### Phase 3: Service Layer Isolation (90% Complete)

- [x] Define service boundaries
- [x] Implement dependency injection
- [x] Add service health checks
- [x] Complete Redis service implementation
- [x] Complete Weaviate service implementation
- [x] Add comprehensive service metrics

### Phase 4: Testing Strategy (85% Complete)

- [x] Add unit tests for ChunkProcessor
- [x] Add base integration test framework
- [x] Add performance test framework
- [x] Implement test utilities and helpers
- 🚧 Complete service integration tests (75% complete)
- 🚧 Complete end-to-end tests (60% complete)
- 🚧 Set up CI pipeline (60% complete)

## Overview

This document outlines the implementation plan for resolving circular imports and improving the dependency structure of the codebase based on dependency graph analysis.

## Phase 1: Package Structure Reorganization

### 1. Create Clear Package Boundaries ✅

```
src/
├── core/           # Core functionality and base classes
│   ├── __init__.py
│   ├── types.py    # Shared type definitions
│   └── errors.py   # Common exceptions
├── config/         # Configuration management
│   ├── __init__.py
│   └── settings.py # Using pydantic_settings
├── services/       # External service integrations
│   ├── __init__.py
│   ├── redis/
│   ├── weaviate/
│   └── supabase/
├── ml/            # Machine learning components
│   ├── __init__.py
│   ├── models/
│   └── pipeline/
└── api/           # FastAPI application
    ├── __init__.py
    ├── routes/
    └── deps/      # FastAPI dependencies
```

### 2. Implement Dependency Injection ✅

```python
# src/core/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(Settings)
    redis = providers.Singleton(RedisService, settings=config)
    weaviate = providers.Singleton(WeaviateClient, settings=config)
```

## Phase 2: Fix Circular Imports

### 1. Extract Interface Definitions ✅

```python
# src/core/interfaces.py
from abc import ABC, abstractmethod
from typing import Protocol

class DataProcessor(Protocol):
    async def process(self, data: Any) -> Any: ...

class StorageBackend(ABC):
    @abstractmethod
    async def store(self, key: str, value: Any) -> None: ...
```

### 2. Implement Forward References ✅

```python
# src/ml/types.py
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from src.ml.models import ModelType
    from src.ml.pipeline import PipelineConfig

T = TypeVar('T')
ModelConfig = TypeVar('ModelConfig', bound='BaseConfig')
```

## Phase 3: Service Layer Isolation ✅

### 1. Create Service Factories ✅

```python
# src/services/factory.py
from typing import Type
from src.core.interfaces import StorageBackend

def create_storage(backend_type: Type[StorageBackend]) -> StorageBackend:
    return backend_type()
```

### 2. Implement Clean Service Boundaries ✅

## Phase 4: Implementation Steps

### 1. Break Circular Dependencies

```bash
# Execute in order:
mkdir -p src/core/interfaces
mkdir -p src/core/types
mkdir -p src/services/base

# Move files:
mv src/pipeline/parameters/base.py src/core/types/parameters.py
mv src/pipeline/validators/* src/core/validators/
```

### 2. Update Import Statements

```python
# Before:
from ..parameters.base import Parameter
from ..validators.numeric import NumericValidator

# After:
from src.core.types.parameters import Parameter
from src.core.validators.numeric import NumericValidator
```

### 3. Create Initialization Order

```python
# src/core/__init__.py
from .types import *
from .errors import *
from .interfaces import *

# Ensure this order in other packages
```

## Phase 5: Testing Strategy

### 1. Create Test Structure

```
tests/
├── unit/
│   ├── core/
│   ├── services/
│   └── ml/
├── integration/
│   ├── services/
│   └── ml/
└── conftest.py    # Shared fixtures
```

### 2. Implementation Order

```bash
# Execute in sequence:
poetry run ruff check src/core --fix
poetry run ruff check src/services --fix
poetry run ruff check src/ml --fix
poetry run ruff check src/api --fix

# Run tests after each step
pytest tests/unit/core
pytest tests/unit/services
pytest tests/unit/ml
pytest tests/integration
```

## Phase 6: Monitoring and Validation

### 1. Add Import Checks

```toml
# pyproject.toml
[tool.ruff.isort]
known-first-party = ["src"]
known-third-party = [
    "fastapi",
    "pydantic",
    "redis",
    "weaviate_client"
]
```

### 2. Implement CI Checks

```yaml
# .github/workflows/ci.yml
- name: Check imports
  run: |
    poetry run ruff check src --select I
```

## Execution Plan

### Day 1: Core Structure

- Create new directory structure
- Move core types and interfaces
- Update base imports

### Day 2: Service Layer

- Implement service factories
- Update service implementations
- Fix service-related imports

### Day 3: ML Components

- Reorganize ML pipeline
- Update ML-related imports
- Implement forward references

### Day 4: API Layer

- Update API dependencies
- Fix route imports
- Implement dependency injection

### Day 5: Testing & Validation

- Update test structure
- Fix test imports
- Run full test suite

## Success Criteria

1. No circular imports detected by `ruff`
2. All tests passing
3. Clean dependency graph with clear hierarchical structure
4. No import-related runtime errors
5. Improved code organization and maintainability
