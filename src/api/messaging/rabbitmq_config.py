"""RabbitMQ configuration settings.

This module defines all configuration settings for RabbitMQ connections,
exchanges, queues, and related functionality. It uses pydantic for validation
and environment variable loading.
"""

from typing import Dict, Optional

from pydantic import AmqpDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQSettings(BaseSettings):
    """RabbitMQ connection and operational settings."""

    # Connection settings
    broker_url: AmqpDsn = Field(
        default="amqp://guest:guest@localhost:5672/", description="RabbitMQ connection URL"
    )
    connection_name: str = Field(
        default="indexforge_service", description="Name of the connection for identification"
    )

    # Connection pool settings
    pool_size: int = Field(default=2, ge=1, le=10, description="Number of connections in the pool")
    max_channels_per_connection: int = Field(
        default=10, ge=1, description="Maximum number of channels per connection"
    )

    # Channel settings
    channel_max_size: int = Field(
        default=0, description="Maximum frame size in bytes (0 means no limit)"  # 0 means no limit
    )
    publisher_confirms: bool = Field(default=True, description="Enable publisher confirms")

    # Consumer settings
    prefetch_count: int = Field(default=10, ge=1, description="Number of messages to prefetch")
    consumer_timeout: float = Field(default=30.0, ge=0.1, description="Consumer timeout in seconds")

    # Retry settings
    max_retries: int = Field(default=3, ge=0, description="Maximum number of retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, description="Delay between retries in seconds")
    retry_backoff: float = Field(
        default=2.0, ge=1.0, description="Backoff multiplier for retry delays"
    )

    # Exchange settings
    default_exchange_type: str = Field(default="topic", description="Default exchange type")
    dead_letter_exchange: str = Field(default="dlx", description="Dead letter exchange name")

    # SSL/TLS settings
    ssl_enabled: bool = Field(default=False, description="Enable SSL/TLS")
    ssl_verify: bool = Field(default=True, description="Verify SSL certificates")
    ssl_cert_file: Optional[str] = Field(default=None, description="Path to SSL certificate file")
    ssl_key_file: Optional[str] = Field(default=None, description="Path to SSL key file")

    # Monitoring settings
    enable_monitoring: bool = Field(
        default=True, description="Enable monitoring and metrics collection"
    )
    monitoring_interval: float = Field(
        default=30.0, ge=1.0, description="Monitoring interval in seconds"
    )

    model_config = SettingsConfigDict(
        env_prefix="RABBITMQ_",
        env_file=".env",
        case_sensitive=False,
        validate_assignment=True,
        extra="ignore",
    )

    def get_connection_parameters(self) -> Dict[str, any]:
        """Get connection parameters for aio-pika."""
        params = {
            "url": str(self.broker_url),
            "connection_name": self.connection_name,
            "channel_max": self.channel_max_size,
            "publisher_confirms": self.publisher_confirms,
        }

        if self.ssl_enabled:
            params.update(
                {
                    "ssl": self.ssl_enabled,
                    "ssl_verify": self.ssl_verify,
                    "ssl_cert_file": self.ssl_cert_file,
                    "ssl_key_file": self.ssl_key_file,
                }
            )

        return params


# Global instance
rabbitmq_settings = RabbitMQSettings()
