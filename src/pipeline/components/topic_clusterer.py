"""Topic clustering component for document organization.

This module provides functionality for clustering documents based on their topics
using machine learning techniques. It helps organize documents into semantically
related groups for better content organization and discovery.
"""


def cluster_documents(self, documents, n_clusters):
    """Cluster documents into topic-based groups.

    This method applies clustering algorithms to organize documents into
    semantically related groups based on their content and embeddings.

    Args:
        documents (List[Dict]): List of document dictionaries, each containing
            at least 'content' and 'embedding' fields
        n_clusters (int): Number of topic clusters to create

    Returns:
        List[Dict]: The input documents enriched with cluster assignments in
            their metadata

    Raises:
        ValueError: If n_clusters is less than 1 or greater than the number
            of documents
        TypeError: If documents don't contain required fields

    Example:
        ```python
        clusterer = TopicClusterer()
        docs = [
            {"content": "ML text", "embedding": [...]},
            {"content": "AI text", "embedding": [...]}
        ]
        clustered_docs = clusterer.cluster_documents(docs, n_clusters=2)
        ```
    """
    self.cluster(n_clusters=n_clusters)
