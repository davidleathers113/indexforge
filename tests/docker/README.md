# Docker Testing Framework

A comprehensive testing framework for validating Docker configurations across the entire container lifecycle. This framework ensures containers are built, configured, and run according to best practices while maintaining high security and performance standards.

## Test Categories

### 1. Static Analysis (`static/`)

- Dockerfile validation using hadolint
- Security scanning with trivy
- Best practices verification
- Layer optimization checks
- Environment configuration validation

### 2. Build Process (`build/`)

- Build time monitoring
- Image size validation
- Layer count optimization
- Build cache effectiveness
- Build arguments handling
- Multi-stage build verification

### 3. Runtime Validation (`runtime/`)

- Container startup time
- Health check validation
- Resource utilization monitoring
- Non-root user verification
- Process isolation
- File permissions

### 4. Integration Testing (`integration/`)

- Inter-container communication
- Network connectivity
- Volume persistence
- Environment variable handling
- Service dependencies
- API integration

### 5. Performance Testing (`performance/`)

- Load testing
- Memory leak detection
- CPU utilization monitoring
- Concurrent connection handling
- Resource limits compliance

## Prerequisites

Install dependencies using Poetry:

```bash
# Install Docker testing dependencies
poetry install --with docker,ci,dev

# Or if you want just the Docker testing dependencies
poetry install --with docker
```

Additional requirements:

- Docker Engine
- hadolint (for Dockerfile linting)
- trivy (for security scanning)

## Running Tests

Run all Docker tests:

```bash
poetry run pytest tests/docker
```

Run specific test category:

```bash
poetry run pytest tests/docker/static/
poetry run pytest tests/docker/build/
poetry run pytest tests/docker/runtime/
poetry run pytest tests/docker/integration/
poetry run pytest tests/docker/performance/
```

## Test Configuration

Key test parameters can be configured through environment variables:

```bash
export MAX_BUILD_TIME=600          # Maximum allowed build time in seconds
export MAX_IMAGE_SIZE_MB=1000      # Maximum allowed image size in MB
export MAX_STARTUP_TIME=10         # Maximum container startup time in seconds
export MAX_MEMORY_GROWTH_MB=50     # Maximum allowed memory growth in MB
export MAX_CPU_PERCENT=80          # Maximum CPU utilization percentage
```

## Test Reports

Test results are provided in multiple formats:

- Console output with detailed failure information
- JUnit XML report for CI integration
- HTML report with performance metrics
- JSON report for automated analysis

## Best Practices

1. **Static Analysis**

   - Use specific base image versions
   - Minimize layer count
   - Follow security best practices
   - Proper environment configuration

2. **Build Process**

   - Optimize build cache usage
   - Minimize image size
   - Use multi-stage builds
   - Handle build arguments properly

3. **Runtime**

   - Implement health checks
   - Run as non-root user
   - Set appropriate permissions
   - Monitor resource usage

4. **Integration**

   - Test service dependencies
   - Verify network isolation
   - Ensure data persistence
   - Validate environment configuration

5. **Performance**
   - Monitor memory usage
   - Track CPU utilization
   - Test concurrent connections
   - Verify resource limits

## Troubleshooting

Common issues and solutions:

1. **Build Failures**

   - Check Dockerfile syntax
   - Verify build context
   - Review resource limits
   - Check network connectivity

2. **Test Failures**

   - Review test logs
   - Check container logs
   - Verify resource availability
   - Validate test environment

3. **Performance Issues**
   - Monitor system resources
   - Check for resource contention
   - Review container limits
   - Analyze performance metrics

## Contributing

1. Follow the existing test structure
2. Add comprehensive docstrings
3. Include appropriate assertions
4. Add new test cases to relevant categories
5. Update documentation as needed

## License

MIT License
