# ADR 001: Service Layer Boundaries and Architectural Organization

## Status

Accepted

## Context

The project has multiple architectural patterns across different components:

- Service-oriented architecture in `src/services/`
- Domain-driven design in `src/core/`
- ML-specific implementations in `src/ml/`
- Pipeline orchestration in `src/pipeline/`
- External integrations in `src/connectors/`

Initially, we considered migrating all components to follow the service architecture pattern. This decision record captures our analysis and decision regarding architectural boundaries.

## Decision

### 1. Service Layer Scope

The service layer (`src/services/`) will be reserved for:

- Infrastructure concerns (storage, caching, databases)
- Cross-cutting concerns (metrics, monitoring)
- External service integrations (Redis, Weaviate)
- ML service implementations

### 2. Domain Layer Preservation

The following will remain as domain-specific architectures:

- Core business logic (`src/core/`)
- Pipeline orchestration (`src/pipeline/`)
- Domain-specific processors
- Connector implementations

### 3. ML Component Organization

ML components will be organized as follows:

- Infrastructure concerns → `src/services/ml/`
- Domain logic → `src/ml/`
- Processing strategies → `src/ml/processing/`

## Rationale

### Why Not Migrate Everything to Services?

1. **Domain Clarity**

   - Different components serve different purposes
   - Not everything is inherently a service
   - Domain logic benefits from domain-driven design

2. **Architectural Fitness**

   - Services best suit infrastructure concerns
   - Pipeline needs workflow architecture
   - Core needs domain-driven architecture

3. **Complexity Management**
   - Over-servicification increases complexity
   - Current boundaries are mostly logical
   - Mixed architecture can be more maintainable

## Consequences

### Positive

1. **Clearer Boundaries**

   - Services handle infrastructure
   - Core handles business logic
   - ML handles machine learning
   - Pipeline handles orchestration

2. **Reduced Complexity**

   - No forced architectural uniformity
   - Natural fit for each component
   - Easier maintenance

3. **Better Organization**
   - Clear service boundaries
   - Logical domain separation
   - Improved maintainability

### Negative

1. **Multiple Patterns**

   - Team needs to understand different patterns
   - Documentation becomes more important
   - Potential for confusion

2. **Integration Points**
   - Need clear interfaces between patterns
   - Careful dependency management required
   - Potential for architectural drift

## Implementation Guidelines

### 1. Service Candidates

Components should be implemented as services if they:

- Provide infrastructure capabilities
- Handle cross-cutting concerns
- Manage external service integration
- Require lifecycle management

### 2. Domain Components

Components should remain domain-specific if they:

- Implement core business logic
- Handle domain-specific processing
- Manage workflow orchestration
- Deal with domain models

### 3. Decision Criteria

When evaluating new components:

1. Is it infrastructure or cross-cutting?
   - Yes → Service architecture
   - No → Continue evaluation
2. Is it core business logic?
   - Yes → Domain architecture
   - No → Continue evaluation
3. Is it workflow orchestration?
   - Yes → Pipeline architecture
   - No → Continue evaluation
4. Does it integrate external systems?
   - Yes → Connector architecture
   - No → Choose based on primary responsibility
