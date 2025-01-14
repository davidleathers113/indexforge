# Dependency Refactoring Implementation Plan

## Overview

This document outlines the implementation plan for resolving circular imports and improving the dependency structure of the codebase based on dependency graph analysis.

## Phase 1: Package Structure Reorganization

### 1. Create Clear Package Boundaries

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

### 2. Implement Dependency Injection

```python
# src/core/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(Settings)
    redis = providers.Singleton(RedisService, settings=config)
    weaviate = providers.Singleton(WeaviateClient, settings=config)
```

## Phase 2: Fix Circular Imports

### 1. Extract Interface Definitions

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

### 2. Implement Forward References

```python
# src/ml/types.py
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from src.ml.models import ModelType
    from src.ml.pipeline import PipelineConfig

T = TypeVar('T')
ModelConfig = TypeVar('ModelConfig', bound='BaseConfig')
```

## Phase 3: Service Layer Isolation

### 1. Create Service Factories

```python
# src/services/factory.py
from typing import Type
from src.core.interfaces import StorageBackend

def create_storage(backend_type: Type[StorageBackend]) -> StorageBackend:
    return backend_type()
```

### 2. Implement Clean Service Boundaries

```python
# src/services/base.py
from abc import ABC, abstractmethod

class BaseService(ABC):
    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def cleanup(self) -> None: ...
```

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
