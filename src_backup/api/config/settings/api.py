"""API server settings configuration."""


from pydantic import Field

from src.api.config.settings import BaseAppSettings


class APISettings(BaseAppSettings):
    """API server settings."""

    # Core API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Document API"
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    VERSION: str = "0.1.0"

    # Deployment Settings
    DEPLOYMENT_REGION: str = "us-west"
    DEBUG: bool = Field(False, env="DEBUG")
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    API_WORKERS: int = Field(1, env="API_WORKERS")
    API_RELOAD: bool = Field(True, env="API_RELOAD")

    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",  # React default port
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
