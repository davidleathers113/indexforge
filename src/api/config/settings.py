"""Configuration settings for the API."""

import os
from functools import lru_cache
from typing import Dict, List, Optional
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, Field, SecretStr, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API settings managed through environment variables."""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Document API"
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    VERSION: str = "0.1.0"

    # Deployment
    DEPLOYMENT_REGION: str = "us-west"
    DEBUG: bool = Field(False, env="DEBUG")
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    API_WORKERS: int = Field(1, env="API_WORKERS")
    API_RELOAD: bool = Field(True, env="API_RELOAD")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React default port
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: Optional[str] = None

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # Sentry
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: Optional[float] = None  # If None, uses dynamic sampling
    SENTRY_PROFILES_SAMPLE_RATE: float = 1.0
    SENTRY_SEND_DEFAULT_PII: bool = False
    SENTRY_MAX_BREADCRUMBS: int = 50
    SENTRY_ATTACH_STACKTRACE: bool = True
    SENTRY_REQUEST_BODIES: str = "small"  # Options: "never", "small", "always"
    SENTRY_WITH_LOCALS: bool = True

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ENABLE_TRACING: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://jaeger:4317"
    OTEL_EXPORTER_OTLP_INSECURE: bool = True

    # Performance Thresholds
    PERFORMANCE_THRESHOLDS: Dict[str, float] = {
        "p95_latency_ms": 500.0,  # 95th percentile latency threshold in milliseconds
        "error_rate_threshold": 0.01,  # 1% error rate threshold
        "apdex_threshold": 0.95,  # Apdex score threshold
    }

    # Database
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False  # SQL query logging

    # Cache
    CACHE_TTL: int = 3600  # Default cache TTL in seconds
    CACHE_MAX_MEMORY: str = "1gb"
    CACHE_POLICY: str = "allkeys-lru"

    # Supabase Configuration
    SUPABASE_URL: str = Field("http://localhost:54321", env="SUPABASE_URL")  # Default to local dev
    SUPABASE_DB_URL: Optional[str] = Field(None, env="SUPABASE_DB_URL")  # PostgreSQL connection URL
    SUPABASE_KEY: SecretStr = Field("dummy-key", env="SUPABASE_KEY")
    SUPABASE_JWT_SECRET: SecretStr = Field("test-jwt-secret", env="SUPABASE_JWT_SECRET")

    # OAuth Configuration - Optional in test environment
    GOOGLE_CLIENT_ID: Optional[str] = Field(None, env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[SecretStr] = Field(None, env="GOOGLE_CLIENT_SECRET")
    GITHUB_CLIENT_ID: Optional[str] = Field(None, env="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[SecretStr] = Field(None, env="GITHUB_CLIENT_SECRET")
    OAUTH_REDIRECT_URL: Optional[AnyHttpUrl] = Field(None, env="OAUTH_REDIRECT_URL")

    # Security
    SECRET_KEY: str = "development_key"  # Update for production

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Allow extra fields in environment variables
    )

    @validator("SUPABASE_URL", pre=True)
    def validate_supabase_url(cls, v: str) -> str:
        """Validate and transform Supabase URL format."""
        if cls._is_test_environment():
            return "http://localhost:54321"

        # If it's a PostgreSQL URL, try to extract the host and convert to HTTP
        parsed = urlparse(v)
        if parsed.scheme == "postgresql":
            # Extract host from PostgreSQL URL and convert to HTTP URL
            host = parsed.hostname
            if host and "supabase" in host:
                project_id = host.split(".")[0]
                return f"https://{project_id}.supabase.co"
            return "http://localhost:54321"  # Fallback to local dev

        # Normal validation for non-PostgreSQL URLs
        if parsed.scheme not in ("http", "https"):
            return "http://localhost:54321"  # Fallback to local dev
        return v

    @validator("SUPABASE_DB_URL", pre=True)
    def validate_supabase_db_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate Supabase database URL format."""
        if v is None:
            # If SUPABASE_DB_URL is not set but SUPABASE_URL is a PostgreSQL URL,
            # use that as the DB URL
            supabase_url = os.getenv("SUPABASE_URL", "")
            if supabase_url.startswith("postgresql://"):
                return supabase_url
            return None

        if cls._is_test_environment():
            return v

        parsed = urlparse(v)
        if parsed.scheme != "postgresql":
            raise ValueError("SUPABASE_DB_URL must use postgresql scheme")
        return v

    @classmethod
    def _is_test_environment(cls) -> bool:
        """Check if running in test environment."""
        return os.getenv("ENVIRONMENT", "").lower() in ("test", "testing")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
