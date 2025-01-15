# Architecture Overview

## Core Design Principles

IndexForge follows a clean architecture pattern with strict dependency rules and interface-based design. The core principles are:

1. **Interface Segregation**: All services are defined by interfaces in the core layer
2. **Dependency Inversion**: Implementation details depend on abstractions
3. **Forward References**: Type hints use forward references to prevent circular imports
4. **Dependency Injection**: Services are wired together using a container

## Directory Structure

```
src/
├── core/
│   ├── __init__.py
│   ├── interfaces.py     # Core service interfaces
│   ├── settings.py       # Application settings
│   └── container.py      # Dependency injection container
├── services/
│   ├── redis.py         # Cache service implementation
│   └── weaviate.py      # Vector service implementation
└── api/
    └── routers/         # API endpoints using injected services
```

## Interface Design

### Service Interfaces

Core service interfaces are defined in `src/core/interfaces.py`:

```python
class CacheService(ABC):
    """Interface for caching services."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]: ...

    @abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

class VectorService(ABC):
    """Interface for vector database services."""

    @abstractmethod
    async def add_object(
        self, class_name: str, data_object: Dict[str, Any], vector: Optional[List[float]] = None
    ) -> str: ...

    @abstractmethod
    async def get_object(self, class_name: str, uuid: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    async def delete_object(self, class_name: str, uuid: str) -> None: ...
```

### Type Safety

We use forward references and type checking to maintain type safety without circular imports:

```python
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from src.core.settings import Settings

SettingsType = TypeVar("SettingsType", bound="Settings")
```

## Dependency Resolution Strategy

### Core Principles

1. **Strict Dependency Direction**:

   - Core interfaces know nothing about implementations
   - Services depend on interfaces, not concrete types
   - Settings are injected, not imported directly

2. **Import Time vs Runtime**:

   - Use `TYPE_CHECKING` for type hints at import time
   - Resolve concrete implementations at runtime through DI
   - Avoid circular dependencies with forward references

3. **Layer Separation**:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Core     │ ◄── │  Services   │ ◄── │    API      │
│ Interfaces  │     │    Layer    │     │  Endpoints  │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Resolution Flow

1. **Interface Definition** (`src/core/interfaces.py`):

   - Define abstract contracts
   - Use forward references for types
   - Keep dependencies minimal

2. **Service Implementation** (`src/services/`):

   - Implement core interfaces
   - Accept settings through constructor
   - Handle concrete dependencies

3. **Dependency Injection** (`src/core/container.py`):

   - Wire implementations to interfaces
   - Manage lifecycle of services
   - Configure runtime dependencies

4. **Usage in API** (`src/api/`):
   - Depend on interfaces only
   - Use dependency injection
   - Maintain loose coupling

## Dependency Injection

The application uses `dependency-injector` for managing service lifecycles and dependencies:

### Container Configuration

```python
class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""

    # Core configuration
    config = providers.Singleton(Settings)

    # Service providers
    cache = providers.Singleton(
        RedisService,
        settings=config,
    )

    vector_db = providers.Singleton(
        WeaviateClient,
        settings=config,
    )

    # Wire modules for automatic injection
    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.api.routers.health",
            "src.api.routers.search",
        ]
    )
```

### Service Implementation

Services accept dependencies through their constructor:

```python
class RedisService(CacheService):
    """Redis implementation of CacheService."""

    def __init__(self, settings: "Settings") -> None:
        self._redis = redis.from_url(
            str(settings.redis_url),
            decode_responses=True
        )
```

### FastAPI Integration

Endpoints use dependency injection through FastAPI's dependency system:

```python
@router.get("/health")
async def health_check(
    cache: CacheService = Depends(Provide[Container.cache]),
    vector_db: VectorService = Depends(Provide[Container.vector_db]),
) -> Dict[str, Any]:
    """Check health of all services."""
    return {
        "cache": await cache.get("health"),
        "vector_db": await vector_db.get_object("health", "status")
    }
```

## Implementation Patterns

### Interface Implementation

1. **Proper Implementation**:

```python
class WeaviateClient(VectorService):
    """Good: Implements interface fully with proper typing."""

    def __init__(self, settings: "Settings") -> None:
        self._client = self._setup_client(settings)

    async def add_object(
        self,
        class_name: str,
        data_object: Dict[str, Any],
        vector: Optional[List[float]] = None
    ) -> str:
        """Fully typed implementation with all parameters."""
        return await self._client.add(class_name, data_object, vector)
```

2. **Anti-patterns to Avoid**:

```python
class BadService(CacheService):  # Don't do this
    """Bad: Incomplete implementation, missing type hints."""

    def __init__(self, settings):  # Missing type hint
        self.settings = settings

    async def get(self, key):  # Missing return type
        pass  # Incomplete implementation
```

### Dependency Resolution

1. **Forward References**:

```python
if TYPE_CHECKING:
    from src.core.settings import Settings
    from src.core.interfaces import CacheService

def setup_cache(settings: "Settings") -> "CacheService":
    """Good: Uses forward references to avoid circular imports."""
    return RedisService(settings)
```

2. **Factory Pattern**:

```python
class ServiceFactory:
    """Good: Factory pattern for service creation."""

    @staticmethod
    def create_cache_service(settings: "Settings") -> CacheService:
        return RedisService(settings)

    @staticmethod
    def create_vector_service(settings: "Settings") -> VectorService:
        return WeaviateClient(settings)
```

### Common Issues and Solutions

1. **Circular Imports**:

   - Problem: Direct imports between modules
   - Solution: Use forward references and TYPE_CHECKING

2. **Runtime Type Errors**:

   - Problem: Missing runtime type information
   - Solution: Ensure proper interface implementation

3. **Dependency Resolution Order**:

   - Problem: Services initialized before dependencies
   - Solution: Use dependency injection container

4. **Testing**:
   - Problem: Hard to mock services
   - Solution: Depend on interfaces, use factory pattern

## Service Layer Architecture

The service layer provides a clean separation between core business logic and external integrations. This isolation is achieved through a combination of factories, base classes, and strict interface boundaries.

### Service Layer Structure

```
src/services/
├── __init__.py
├── base.py          # Base service definitions
├── factory.py       # Service factory implementations
├── redis.py         # Cache service implementation
└── weaviate.py      # Vector service implementation
```

### Base Service Contract

All services implement a common base contract:

```python
class BaseService(ABC):
    """Base contract for all services."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service connections and resources."""
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up service resources and connections."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check service health status."""
        ...
```

### Service Factory Pattern

Services are created through factories to ensure proper initialization and dependency injection:

```python
class ServiceFactory:
    """Factory for creating service instances."""

    @classmethod
    def create_cache_service(
        cls,
        settings: "Settings",
        service_type: Type[CacheService] = RedisService
    ) -> CacheService:
        """Create a cache service instance."""
        service = service_type(settings)
        await service.initialize()
        return service

    @classmethod
    def create_vector_service(
        cls,
        settings: "Settings",
        service_type: Type[VectorService] = WeaviateClient
    ) -> VectorService:
        """Create a vector service instance."""
        service = service_type(settings)
        await service.initialize()
        return service
```

### Service Implementation Example

Example of a properly isolated service implementation:

```python
class RedisService(CacheService, BaseService):
    """Redis implementation with proper isolation."""

    def __init__(self, settings: "Settings") -> None:
        self._settings = settings
        self._client: Optional[Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        self._client = redis.from_url(
            str(self._settings.redis_url),
            decode_responses=True
        )
        await self._client.ping()  # Verify connection

    async def cleanup(self) -> None:
        """Clean up Redis resources."""
        if self._client:
            await self._client.close()
            self._client = None

    async def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            await self._client.ping()
            return True
        except RedisError:
            return False

    # CacheService interface implementation
    async def get(self, key: str) -> Optional[str]:
        if not self._client:
            raise ServiceNotInitializedError()
        return await self._client.get(key)
```

### Service Lifecycle Management

Services follow a strict lifecycle:

1. **Creation**: Through factory methods
2. **Initialization**: Explicit async initialization
3. **Usage**: Through interface methods
4. **Cleanup**: Proper resource cleanup
5. **Health Monitoring**: Regular health checks

### Testing Services

Services are designed for testability:

```python
class MockCacheService(CacheService, BaseService):
    """Mock implementation for testing."""

    def __init__(self) -> None:
        self._store: Dict[str, str] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True

    async def cleanup(self) -> None:
        self._store.clear()
        self._initialized = False

    async def health_check(self) -> bool:
        return self._initialized

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)
```

### Best Practices

1. **Initialization**:

   - Always use factory methods
   - Never skip initialization
   - Handle connection failures gracefully

2. **Resource Management**:

   - Clean up resources explicitly
   - Use context managers when appropriate
   - Monitor resource usage

3. **Error Handling**:

   - Define service-specific exceptions
   - Provide meaningful error messages
   - Log service state changes

4. **Testing**:
   - Use mock implementations
   - Test lifecycle methods
   - Verify resource cleanup
