# IndexForge New Migrations

## Overview

This document outlines the detailed migration plan for restructuring the IndexForge codebase to align with the target architecture. The plan addresses component dependencies, testing requirements, and maintains system stability throughout the migration process.

## Current State Analysis

### Core Components Location Issues

1. ML Components in Core:

   - `src/core/tracking/` contains ML-related tracking
   - `src/core/schema/` has ML schema definitions
   - These need migration to `src/ml/`

2. Circular Dependencies:

   - Between `src/core/tracking` and `src/core/lineage`
   - Between `src/core/models` and `src/core/schema`
   - Between `src/services` and `src/core`

3. Duplicate Functionality:
   - Configuration in both `src/api/config` and `src/config`
   - Utilities spread across multiple directories
   - Multiple validation implementations

## Target Structure

```
src/
├── core/                  # Core functionality and base classes
│   ├── interfaces/        # Core interfaces and protocols
│   ├── models/           # Domain models
│   ├── validation/       # Core validation logic
│   ├── schema/           # Core schema definitions
│   └── utils/            # Core utilities
├── config/               # Centralized configuration
│   ├── logging/          # Logging configuration
│   ├── settings/         # Application settings
│   └── validation/       # Config validation
├── services/             # External service integrations
│   ├── redis/           # Redis service
│   ├── weaviate/        # Weaviate service
│   └── storage/         # Storage services
├── ml/                   # Machine learning components
│   ├── embeddings/       # Embedding generation
│   ├── pipeline/        # ML pipeline components
│   ├── processing/      # Text processing
│   ├── tracking/        # ML tracking (moved from core)
│   └── models/          # ML models
└── api/                  # FastAPI application
    ├── routes/          # API routes
    ├── models/          # API models
    ├── services/        # API services
    └── dependencies/    # FastAPI dependencies
```

## Migration Phases

### Phase 1: Foundation (Week 1)

#### 1. Core Interface Definition

- Create `src/core/interfaces/`
- Move all interfaces and protocols
- Define clear boundaries between components
- Update existing imports
- Estimated time: 2 days
- Testing: Interface compliance tests

#### 2. Utils Consolidation

- Create unified utils structure
- Move core utilities first
- Categorize by domain (core/ml/api)
- Update all imports
- Estimated time: 2 days
- Testing: Utility function tests

#### 3. Configuration Centralization

- Merge `src/api/config` and `src/config`
- Set up logging configuration
- Create unified settings structure
- Estimated time: 1 day
- Testing: Configuration loading tests

### Phase 2: Core Restructuring (Week 2)

#### 1. Core Models Migration

- Move domain models to `src/core/models/`
- Split ML models to `src/ml/models/`
- Update model relationships
- Estimated time: 2 days
- Testing: Model validation tests

#### 2. Schema Reorganization

- Restructure schema definitions
- Move ML schemas to `src/ml/`
- Update schema relationships
- Estimated time: 2 days
- Testing: Schema validation tests

#### 3. Validation Consolidation

- Move all validation to `src/core/validation/`
- Create unified validation interfaces
- Estimated time: 1 day
- Testing: Validation logic tests

### Phase 3: ML Component Migration (Week 3)

#### 1. ML Foundation

- Set up `src/ml/` structure
- Move embeddings and pipeline
- Create ML interfaces
- Estimated time: 2 days
- Testing: ML component tests

#### 2. Tracking Migration

- Move tracking from core to ML
- Update tracking dependencies
- Resolve circular dependencies
- Estimated time: 2 days
- Testing: Tracking system tests

#### 3. Processing Components

- Move text processing to ML
- Update processing pipeline
- Estimated time: 1 day
- Testing: Processing pipeline tests

### Phase 4: Service Layer (Week 4)

#### 1. Service Interfaces

- Define service boundaries
- Create service protocols
- Estimated time: 1 day
- Testing: Interface tests

#### 2. Implementation Migration

- Move service implementations
- Update service dependencies
- Estimated time: 2 days
- Testing: Service integration tests

#### 3. API Integration

- Update API dependencies
- Finalize service integration
- Estimated time: 2 days
- Testing: End-to-end API tests

## Testing Strategy

### Unit Tests

- Migrate with corresponding components
- Update import paths
- Add new interface tests
- Test isolated components

### Integration Tests

- Test component interactions
- Verify service boundaries
- Test ML pipeline integration
- Test API functionality

### End-to-End Tests

- Full system testing
- API endpoint testing
- ML pipeline testing
- Performance testing

## Dependency Management

### Circular Dependencies

1. Break core/tracking dependency:

   - Create intermediate interfaces
   - Use dependency injection
   - Implement event system

2. Break core/schema dependency:
   - Move shared models to interfaces
   - Use protocol definitions
   - Implement factory pattern

### Import Strategy

- Use relative imports within packages
- Use absolute imports across packages
- Update imports incrementally
- Verify after each phase

## Monitoring and Validation

### Performance Monitoring

- Establish baseline metrics
- Monitor during migration
- Compare after each phase
- Track API response times
- Monitor ML pipeline performance

### Migration Validation

- Run test suite after each component
- Verify API functionality
- Check ML pipeline accuracy
- Validate data consistency
- Monitor error rates

## Rollback Procedures

### Component Level

1. Keep backup of each component
2. Version control checkpoints
3. Component-specific tests
4. Revert procedures

### System Level

1. Full system backup
2. System state checkpoints
3. Integration test suite
4. System restore procedure

## Success Metrics

1. Code Quality

   - No circular dependencies
   - Clear component boundaries
   - Consistent import structure
   - Improved test coverage

2. Performance

   - Equal or better response times
   - Reduced memory usage
   - Improved ML pipeline efficiency
   - Better resource utilization

3. Maintainability
   - Clear package structure
   - Documented interfaces
   - Reduced code duplication
   - Better dependency management

## Risk Mitigation

1. Technical Risks

   - Backup all components before migration
   - Comprehensive test coverage
   - Incremental migration
   - Regular validation

2. Operational Risks

   - Maintain system stability
   - Monitor performance metrics
   - Regular checkpoints
   - Clear rollback procedures

3. Integration Risks
   - Test component interactions
   - Verify API compatibility
   - Check ML pipeline integration
   - Validate data flow
