import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import hvac
from fastapi import HTTPException
from loguru import logger


class VaultManager:
    """Manages interactions with HashiCorp Vault for secrets management."""

    def __init__(self):
        """Initialize Vault client with configuration."""
        self.client = hvac.Client(
            url=os.getenv("VAULT_ADDR", "https://127.0.0.1:8200"),
            token=os.getenv("VAULT_TOKEN"),
            verify=False if os.getenv("ENVIRONMENT") == "development" else True,
        )
        self._initialize_vault()

    def _initialize_vault(self) -> None:
        """Initialize Vault if not already initialized."""
        try:
            if not self.client.sys.is_initialized():
                logger.warning("Vault is not initialized. Initializing now...")
                init_result = self.client.sys.initialize()
                # In production, these should be securely stored and distributed
                logger.info(f"Vault initialized with {len(init_result['keys'])} key shares")
        except Exception as e:
            logger.error(f"Failed to initialize Vault: {str(e)}")
            raise HTTPException(status_code=500, detail="Vault initialization failed")

    async def get_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """Retrieve a secret from Vault.

        Args:
            path: Path to the secret in Vault.

        Returns:
            Dictionary containing the secret data if found, None otherwise.
        """
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(path=path)
            return secret["data"]["data"] if secret else None
        except Exception as e:
            logger.error(f"Failed to retrieve secret at {path}: {str(e)}")
            return None

    async def set_secret(self, path: str, secret: Dict[str, Any]) -> bool:
        """Store a secret in Vault.

        Args:
            path: Path where to store the secret.
            secret: Dictionary containing the secret data.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret,
                metadata={
                    "created_at": datetime.utcnow().isoformat(),
                    "rotation_due": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                },
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set secret at {path}: {str(e)}")
            return False

    async def rotate_secret(self, path: str, new_secret: Dict[str, Any]) -> bool:
        """Rotate a secret in Vault.

        Args:
            path: Path to the secret to rotate.
            new_secret: New secret data to store.

        Returns:
            bool: True if rotation was successful, False otherwise.
        """
        try:
            # Get the current version of the secret
            current = await self.get_secret(path)
            if current is None:
                logger.warning(f"No existing secret found at {path}")
                return await self.set_secret(path, new_secret)

            # Store the new version
            success = await self.set_secret(path, new_secret)
            if success:
                logger.info(f"Successfully rotated secret at {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to rotate secret at {path}: {str(e)}")
            return False

    async def list_secrets(self, path: str) -> Optional[list]:
        """List all secrets under a path.

        Args:
            path: Path to list secrets from.

        Returns:
            List of secret names if successful, None otherwise.
        """
        try:
            result = self.client.secrets.kv.v2.list_secrets(path=path)
            return result["data"]["keys"] if result else None
        except Exception as e:
            logger.error(f"Failed to list secrets at {path}: {str(e)}")
            return None

    async def delete_secret(self, path: str) -> bool:
        """Delete a secret from Vault.

        Args:
            path: Path to the secret to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=path)
            logger.info(f"Successfully deleted secret at {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret at {path}: {str(e)}")
            return False
