"""Enriched chunking system with semantic analysis and topic clustering.

This module combines the paragraph-based chunking system with semantic analysis
and topic clustering to provide enriched chunks with metadata about their
relationships and topic groupings.
"""

from dataclasses import dataclass
from uuid import UUID

from .base import Chunk, ChunkingConfig
from .paragraph import ParagraphChunker
from .semantic import SemanticConfig, SemanticProcessor


@dataclass
class EnrichedChunkingConfig:
    """Configuration for enriched chunking with semantic analysis."""

    chunking_config: ChunkingConfig
    semantic_config: SemanticConfig | None = None
    enable_topic_clustering: bool = True
    min_cluster_size: int = 3
    max_topics: int = 10
    add_topic_metadata: bool = True
    add_similarity_metadata: bool = True


class EnrichedChunker:
    """Chunker that combines paragraph-based chunking with semantic analysis."""

    def __init__(self, config: EnrichedChunkingConfig):
        """Initialize the enriched chunker.

        Args:
            config: Configuration for chunking and semantic analysis
        """
        self.config = config
        self.paragraph_chunker = ParagraphChunker(config.chunking_config)
        if config.semantic_config:
            self.semantic_processor = SemanticProcessor(
                ref_manager=self.paragraph_chunker.ref_manager,
                config=config.semantic_config,
            )
        else:
            self.semantic_processor = None

    def process_text(self, text: str) -> list[dict]:
        """Process text into chunks with semantic enrichment.

        Args:
            text: Text to process

        Returns:
            List of dictionaries containing chunk content and metadata
        """
        # First, perform paragraph-based chunking
        chunks = self.paragraph_chunker.chunk_text(text)
        chunk_ids = {chunk.id for chunk in chunks}

        enriched_chunks = []
        for chunk in chunks:
            chunk_data = {
                "id": chunk.id,
                "content": chunk.content,
                "metadata": chunk.metadata or {},
            }

            # Add semantic enrichment if enabled
            if self.semantic_processor and chunk_ids:
                # Add topic clustering metadata
                if (
                    self.config.enable_topic_clustering
                    and len(chunk_ids) >= self.config.min_cluster_size
                ):
                    topics = self.semantic_processor.analyze_topic_relationships(
                        chunk_ids, num_topics=min(self.config.max_topics, len(chunk_ids) // 2)
                    )
                    if self.config.add_topic_metadata:
                        for topic_label, topic_chunks in topics.items():
                            if chunk.id in topic_chunks:
                                chunk_data["metadata"]["topic"] = topic_label
                                break

                # Add similarity metadata
                if self.config.add_similarity_metadata:
                    similar_chunks = self.semantic_processor.find_similar_chunks(chunk.id)
                    if similar_chunks:
                        chunk_data["metadata"]["similar_chunks"] = [
                            {"id": c_id, "similarity": score} for c_id, score in similar_chunks
                        ]

                # Add semantic relationships
                relationships = self.semantic_processor.detect_semantic_relationships(chunk.id)
                for ref_type, refs in relationships.items():
                    if refs:  # Only add non-empty relationships
                        chunk_data["metadata"][f"related_{ref_type.name.lower()}"] = [
                            {"id": c_id, "score": score} for c_id, score in refs
                        ]

            enriched_chunks.append(chunk_data)

        return enriched_chunks

    def batch_process_texts(self, texts: list[str]) -> list[list[dict]]:
        """Process multiple texts in batch, maintaining relationships across all chunks.

        Args:
            texts: List of texts to process

        Returns:
            List of lists of enriched chunks, one list per input text
        """
        all_chunks = []
        chunk_groups = []

        # First pass: Create all chunks
        for text in texts:
            chunks = self.paragraph_chunker.chunk_text(text)
            all_chunks.extend(chunks)
            chunk_groups.append([chunk.id for chunk in chunks])

        # Second pass: Enrich chunks with semantic information
        if self.semantic_processor and self.config.enable_topic_clustering:
            all_chunk_ids = {chunk.id for chunk in all_chunks}
            if len(all_chunk_ids) >= self.config.min_cluster_size:
                # Analyze topics across all chunks
                topics = self.semantic_processor.analyze_topic_relationships(
                    all_chunk_ids, num_topics=min(self.config.max_topics, len(all_chunk_ids) // 2)
                )

                # Create enriched chunks for each text
                enriched_groups = []
                for group_ids in chunk_groups:
                    group_chunks = []
                    for chunk_id in group_ids:
                        chunk = next(c for c in all_chunks if c.id == chunk_id)
                        chunk_data = self._enrich_chunk(chunk, topics, all_chunk_ids)
                        group_chunks.append(chunk_data)
                    enriched_groups.append(group_chunks)
                return enriched_groups

        # If semantic processing is disabled or not enough chunks
        return [
            [{"id": c.id, "content": c.content, "metadata": c.metadata or {}}] for c in all_chunks
        ]

    def _enrich_chunk(
        self, chunk: "Chunk", topics: dict[str, set[UUID]], all_chunk_ids: set[UUID]
    ) -> dict:
        """Enrich a single chunk with semantic metadata.

        Args:
            chunk: Chunk to enrich
            topics: Topic mapping from analyze_topic_relationships
            all_chunk_ids: Set of all chunk IDs for relationship detection

        Returns:
            Dictionary containing chunk data and metadata
        """
        chunk_data = {
            "id": chunk.id,
            "content": chunk.content,
            "metadata": chunk.metadata or {},
        }

        # Add topic metadata
        if self.config.add_topic_metadata:
            for topic_label, topic_chunks in topics.items():
                if chunk.id in topic_chunks:
                    chunk_data["metadata"]["topic"] = topic_label
                    break

        # Add similarity and relationship metadata
        if self.config.add_similarity_metadata:
            similar_chunks = self.semantic_processor.find_similar_chunks(chunk.id)
            if similar_chunks:
                chunk_data["metadata"]["similar_chunks"] = [
                    {"id": c_id, "similarity": score} for c_id, score in similar_chunks
                ]

            relationships = self.semantic_processor.detect_semantic_relationships(chunk.id)
            for ref_type, refs in relationships.items():
                if refs:
                    chunk_data["metadata"][f"related_{ref_type.name.lower()}"] = [
                        {"id": c_id, "score": score} for c_id, score in refs
                    ]

        return chunk_data
