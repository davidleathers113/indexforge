# Fixture Responsibilities

## Core Infrastructure

### core/

- Base state management and core functionality
- Error handling and tracking
- Logging utilities
- **Components:**
  - `__init__.py`: Core module entry point
  - `base.py`: Base state class and core functionality
  - `errors.py`: Error handling and types
  - `logger.py`: Logging fixtures
- **Dependencies:** None

## Data Management

### data/

- Data storage and manipulation
- Cache management
- Vector operations
- Embedding generation
- **Components:**
  - `__init__.py`: Data module entry point
  - `cache.py`: Cache management
  - `vector.py`: Vector operations
  - `embedding.py`: Embedding generation
- **Dependencies:** core

### documents/

- Document management and processing
- State tracking
- Sample data generation
- **Components:**
  - `__init__.py`: Documents module entry point
  - `state.py`: Document state management
  - `processor.py`: Document processing
  - `fixtures.py`: Sample documents and test data
- **Dependencies:** core

## Processing & Analysis

### processing/

- Text and data processing
- Analysis utilities
- Clustering functionality
- **Components:**
  - `__init__.py`: Processing module entry point
  - `pii.py`: PII detection and redaction
  - `topic.py`: Topic clustering
  - `kmeans.py`: KMeans clustering
- **Dependencies:** core, numpy

### text/

- Text processing utilities
- Encoding and tokenization
- Summarization
- **Components:**
  - `__init__.py`: Text module entry point
  - `processor.py`: Text processing
  - `summarizer.py`: Text summarization
- **Dependencies:** core

## Search & Schema

### search/

- Search functionality
- Query processing
- Result ranking
- **Components:**
  - `__init__.py`: Search module entry point
  - `executor.py`: Search execution
  - `components.py`: Search components
- **Dependencies:** core, data

### schema/

- Schema validation and migration
- Version management
- **Components:**
  - `__init__.py`: Schema module entry point
  - `validator.py`: Schema validation
  - `migrator.py`: Schema migration
- **Dependencies:** core

## System Components

### system/

- System-level functionality
- CLI and components
- Monitoring and pipeline
- **Components:**
  - `__init__.py`: System module entry point
  - `cli.py`: CLI fixtures
  - `components.py`: Component management
  - `monitoring.py`: System monitoring
  - `pipeline.py`: Pipeline management
- **Dependencies:** core

## Configuration

### constants.py

- Shared test constants
- Configuration values
- Environment settings
- **Used by:** All modules

## Documentation

### mock_fixtures.md

- Documentation for mock fixture patterns
- Usage examples
- Best practices
- Implementation guidelines

## Shared Functionality Patterns

1. **State Management**

   - All state classes inherit from `BaseState`
   - Common reset and error tracking
   - Consistent initialization patterns

2. **Error Handling**

   - Centralized error types in core/errors.py
   - Standardized error reporting
   - Common error tracking methods

3. **Mock Patterns**

   - Consistent use of MagicMock
   - Standard fixture scoping (function)
   - State cleanup in fixture teardown

4. **Configuration**

   - Shared constants
   - Common test settings
   - Environment management

5. **Utility Functions**
   - Shared helper methods
   - Common test data generation
   - Reusable assertions

## Module Organization

1. **Entry Points**

   - Each module has a clear entry point in **init**.py
   - Re-exports public interfaces
   - Maintains backward compatibility

2. **State Management**

   - Each module has its own state class(es)
   - State classes follow consistent patterns
   - Clear state initialization and cleanup

3. **Dependencies**

   - Clearly documented dependencies
   - Minimal cross-module dependencies
   - Core module as foundation

4. **Testing**
   - Each module has its own test suite
   - Proper cleanup in fixtures
   - Isolation between tests
