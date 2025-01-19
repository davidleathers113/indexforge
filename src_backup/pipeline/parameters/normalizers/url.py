"""URL normalizer implementation."""

import logging
from urllib.parse import urlparse, urlunparse

from src.pipeline.parameters.normalizers.base import Normalizer


class URLNormalizer(Normalizer[str, str]):
    """Normalizer for URL values."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def normalize(self, value: str) -> str:
        """Normalize a URL value.

        Args:
            value: URL to normalize

        Returns:
            Normalized URL string
        """
        try:
            parsed = urlparse(value)
            scheme = parsed.scheme.lower()
            path = parsed.path.rstrip("/")  # Remove trailing slash without adding /
            normalized = urlunparse((scheme, parsed.netloc, path, "", "", ""))
            self.logger.debug(f"Normalized URL {value} to {normalized}")
            return normalized
        except Exception as e:
            self.logger.warning(f"Failed to normalize URL {value}: {e!s}")
            return value
