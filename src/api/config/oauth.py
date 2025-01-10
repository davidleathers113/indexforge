"""OAuth configuration settings."""

from typing import Dict

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class OAuthProviderConfig(BaseModel):
    """OAuth provider configuration."""

    client_id: str
    client_secret: str
    scopes: str
    authorize_url: str
    token_url: str
    userinfo_url: str


class OAuthSettings(BaseSettings):
    """OAuth settings."""

    google_client_id: str
    google_client_secret: str
    github_client_id: str
    github_client_secret: str
    oauth_redirect_url: str = "http://localhost:8000/api/v1/auth/callback"

    @property
    def providers(self) -> Dict[str, OAuthProviderConfig]:
        """Get OAuth provider configurations.

        Returns:
            Dict of provider configurations
        """
        return {
            "google": OAuthProviderConfig(
                client_id=self.google_client_id,
                client_secret=self.google_client_secret,
                scopes="email profile",
                authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
            ),
            "github": OAuthProviderConfig(
                client_id=self.github_client_id,
                client_secret=self.github_client_secret,
                scopes="read:user user:email",
                authorize_url="https://github.com/login/oauth/authorize",
                token_url="https://github.com/login/oauth/access_token",
                userinfo_url="https://api.github.com/user",
            ),
        }

    class Config:
        """Pydantic model configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
