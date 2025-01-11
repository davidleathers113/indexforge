"""RabbitMQ resource management test package.

This package contains tests for verifying resource management in the RabbitMQ connection manager:
- Resource cleanup (connection/channel cleanup after use)
- Memory leak prevention (proper resource release)
- Graceful shutdown (cleanup during application shutdown)
"""
