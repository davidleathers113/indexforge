"""Dependency injection container module.

This module provides the main dependency injection container that manages
application-wide dependencies and ensures clean separation of concerns.
"""

from dependency_injector import containers, providers

from src.config.settings import Settings
from src.core.security.encryption import EncryptionConfig
from src.core.security.key_storage import KeyStorageConfig
from src.core.security.provider import SecurityServiceProvider
from src.ml.embeddings import EmbeddingGenerator
from src.ml.processing import TextProcessor
from src.ml.search import SemanticSearch
from src.services.redis import RedisService
from src.services.weaviate import WeaviateClient


class Container(containers.DeclarativeContainer):
    """Main dependency injection container.

    This container manages the lifecycle and dependencies of core application services.
    """

    # Configuration
    config = providers.Singleton(Settings)

    # Security Configuration
    key_storage_config = providers.Singleton(
        KeyStorageConfig,
        storage_dir=config.provided.security.key_storage_dir,
        backup_dir=config.provided.security.key_backup_dir,
        storage_key=config.provided.security.storage_key,
        max_backup_count=config.provided.security.max_backup_count,
        enable_atomic_writes=config.provided.security.enable_atomic_writes,
    )

    encryption_config = providers.Singleton(
        EncryptionConfig,
        master_key=config.provided.security.master_key,
        key_rotation_days=config.provided.security.key_rotation_days,
        pbkdf2_iterations=config.provided.security.pbkdf2_iterations,
    )

    # Security Services
    security = providers.Singleton(
        SecurityServiceProvider,
        encryption_config=encryption_config,
        key_storage_config=key_storage_config,
    )

    # Core Services
    cache = providers.Singleton(RedisService, settings=config)

    vector_db = providers.Singleton(WeaviateClient, settings=config)

    # ML Services
    embedding_generator = providers.Singleton(EmbeddingGenerator, settings=config)

    text_processor = providers.Singleton(TextProcessor, settings=config)

    semantic_search = providers.Singleton(
        SemanticSearch, vector_db=vector_db, embedding_generator=embedding_generator
    )

    # Wire modules for automatic dependency injection
    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.api.routers.health",
            "src.api.routers.search",
            "src.api.routers.document",
            "src.services.redis",
            "src.services.weaviate",
            "src.ml.embeddings",
            "src.ml.processing",
            "src.ml.search",
            "src.core.security.provider",  # Add security provider for wiring
        ]
    )
