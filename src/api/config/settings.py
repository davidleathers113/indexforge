"""Configuration settings for the API."""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API settings managed through environment variables."""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Document API"
    ENVIRONMENT: str = "development"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React default port
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: str | None = None

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # OpenAI
    OPENAI_API_KEY: str

    # Sentry
    SENTRY_DSN: str | None = None

    # Security
    SECRET_KEY: str = "development_key"  # Update for production

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
