"""Language validation strategies with caching support."""

import hashlib
from typing import Dict, List, Optional, Set

from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException

from src.core.interfaces import CacheService
from src.ml.processing.models.chunks import Chunk
from src.ml.processing.validation.validators.base import ValidationStrategy


class LanguageValidator(ValidationStrategy):
    """Validates chunk language requirements with caching support."""

    def __init__(
        self,
        supported_languages: Optional[Set[str]] = None,
        cache_service: Optional[CacheService] = None,
        min_content_length: int = 50,
        cache_ttl: int = 3600,  # 1 hour cache TTL
    ) -> None:
        """Initialize language validator.

        Args:
            supported_languages: Set of supported language codes
            cache_service: Optional cache service for language detection results
            min_content_length: Minimum content length for language detection
            cache_ttl: Cache TTL in seconds
        """
        self.supported_languages = supported_languages or {"en"}
        self._cache_service = cache_service
        self._min_content_length = min_content_length
        self._cache_ttl = cache_ttl

    def _generate_cache_key(self, content: str) -> str:
        """Generate cache key for content.

        Args:
            content: Content to generate key for

        Returns:
            str: Cache key
        """
        # Use first 1000 chars for long content to avoid excessive hashing
        content_sample = content[:1000]
        return f"lang_detect:{hashlib.md5(content_sample.encode()).hexdigest()}"

    async def _get_cached_result(self, content: str) -> Optional[Dict]:
        """Get cached language detection result.

        Args:
            content: Content to get result for

        Returns:
            Optional[Dict]: Cached result if exists
        """
        if not self._cache_service:
            return None

        try:
            cache_key = self._generate_cache_key(content)
            cached = await self._cache_service.get(cache_key)
            return cached if cached else None
        except Exception:
            return None

    async def _cache_result(self, content: str, result: Dict) -> None:
        """Cache language detection result.

        Args:
            content: Content that was analyzed
            result: Detection result to cache
        """
        if not self._cache_service:
            return

        try:
            cache_key = self._generate_cache_key(content)
            await self._cache_service.set(cache_key, result, expire=self._cache_ttl)
        except Exception:
            pass  # Fail silently on cache errors

    async def validate(self, chunk: Chunk, metadata: Optional[Dict] = None) -> List[str]:
        """Validate chunk language with caching support.

        Args:
            chunk: Chunk to validate
            metadata: Optional validation metadata

        Returns:
            List of validation error messages
        """
        errors = []

        # Skip validation for very short content
        if len(chunk.content) < self._min_content_length:
            return []

        try:
            # Check cache first
            cached_result = await self._get_cached_result(chunk.content)
            if cached_result:
                primary_lang = cached_result["primary_lang"]
                significant_langs = cached_result["significant_langs"]
            else:
                # Perform language detection
                lang_probabilities = detect_langs(chunk.content)
                primary_lang = detect(chunk.content)
                significant_langs = [lang.lang for lang in lang_probabilities if lang.prob > 0.3]

                # Cache the result
                await self._cache_result(
                    chunk.content,
                    {"primary_lang": primary_lang, "significant_langs": significant_langs},
                )

            if primary_lang not in self.supported_languages:
                errors.append(
                    f"Content language {primary_lang} is not in supported languages {self.supported_languages}"
                )

            # Check for mixed language content
            if len(significant_langs) > 1:
                errors.append(f"Content appears to be multilingual: {significant_langs}")

        except LangDetectException:
            errors.append("Unable to detect content language")

        return errors
