"""Dependency injection container module.

This module provides the main dependency injection container that manages
application-wide dependencies and ensures clean separation of concerns.
"""

from dependency_injector import containers, providers

from src.config.settings import Settings
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
        ]
    )
