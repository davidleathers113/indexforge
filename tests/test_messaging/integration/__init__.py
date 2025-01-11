"""RabbitMQ integration test package.

This package contains integration tests for verifying RabbitMQ functionality in real-world scenarios:
- Basic connectivity (connection establishment, channel creation)
- Network resilience (reconnection, error recovery)
- End-to-end messaging (message publishing, consumption)
- Load scenarios (high message volume, concurrent operations)
- Failure modes (network partitions, broker restarts)

Tests in this package require:
1. A running RabbitMQ instance (provided via Docker)
2. Network access to the RabbitMQ instance
3. Valid credentials and permissions

Note: These tests are designed to run against a real RabbitMQ instance and may take
longer to execute than unit tests. They should be run in a CI environment with appropriate
timeouts and retry mechanisms.
"""
