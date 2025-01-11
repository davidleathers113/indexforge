"""Security and authentication settings configuration."""

from typing import Optional

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator

from src.api.config.settings import BaseAppSettings


class SecuritySettings(BaseAppSettings):
    """Security and authentication settings."""

    # Core Security
    SECRET_KEY: str = Field(
        default="development_key", description="Secret key for cryptographic operations"
    )

    # Supabase Configuration
    SUPABASE_URL: str = Field(
        default="http://localhost:54321", env="SUPABASE_URL", description="Supabase instance URL"
    )
    SUPABASE_DB_URL: Optional[str] = Field(
        default=None, env="SUPABASE_DB_URL", description="PostgreSQL connection URL"
    )
    SUPABASE_KEY: SecretStr = Field(
        default="dummy-key", env="SUPABASE_KEY", description="Supabase API key"
    )
    SUPABASE_JWT_SECRET: SecretStr = Field(
        default="test-jwt-secret",
        env="SUPABASE_JWT_SECRET",
        description="JWT secret for token verification",
    )

    # OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = Field(
        default=None, env="GOOGLE_CLIENT_ID", description="Google OAuth client ID"
    )
    GOOGLE_CLIENT_SECRET: Optional[SecretStr] = Field(
        default=None, env="GOOGLE_CLIENT_SECRET", description="Google OAuth client secret"
    )
    GITHUB_CLIENT_ID: Optional[str] = Field(
        default=None, env="GITHUB_CLIENT_ID", description="GitHub OAuth client ID"
    )
    GITHUB_CLIENT_SECRET: Optional[SecretStr] = Field(
        default=None, env="GITHUB_CLIENT_SECRET", description="GitHub OAuth client secret"
    )
    OAUTH_REDIRECT_URL: Optional[AnyHttpUrl] = Field(
        default=None, env="OAUTH_REDIRECT_URL", description="OAuth redirect URL"
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is secure in production."""
        if not cls._is_test_environment() and v == "development_key":
            raise ValueError("Must set a secure SECRET_KEY in production")
        return v

    @field_validator("SUPABASE_URL")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        """Validate Supabase URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("SUPABASE_URL must start with http:// or https://")
        return v

    @field_validator("SUPABASE_DB_URL")
    @classmethod
    def validate_supabase_db_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate Supabase database URL format."""
        if v is not None and not v.startswith("postgresql://"):
            raise ValueError("SUPABASE_DB_URL must start with postgresql://")
        return v
