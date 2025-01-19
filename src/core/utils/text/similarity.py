"""Text similarity utilities.

This module provides functions for computing text similarity using various
methods including TF-IDF and cosine similarity.
"""

from typing import List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_text_similarity(text1: str, text2: str, method: str = "tfidf") -> float:
    """Calculate similarity between two text strings.

    Args:
        text1: First text string
        text2: Second text string
        method: Similarity method ('tfidf' or 'jaccard')

    Returns:
        Similarity score between 0 and 1

    Raises:
        ValueError: If texts are empty or method is invalid
    """
    if not text1 or not text2:
        raise ValueError("Both texts must be non-empty")

    if method == "tfidf":
        return _tfidf_similarity(text1, text2)
    elif method == "jaccard":
        return _jaccard_similarity(text1, text2)
    else:
        raise ValueError(f"Unsupported similarity method: {method}")


def find_similar_texts(
    query: str,
    texts: List[str],
    threshold: float = 0.5,
    method: str = "tfidf",
    top_k: Optional[int] = None,
) -> List[tuple[int, float]]:
    """Find similar texts from a collection.

    Args:
        query: Query text to compare against
        texts: List of texts to search in
        threshold: Minimum similarity threshold
        method: Similarity method ('tfidf' or 'jaccard')
        top_k: Optional limit on number of results

    Returns:
        List of tuples containing (text_index, similarity_score)
        sorted by similarity in descending order

    Raises:
        ValueError: If inputs are invalid
    """
    if not query or not texts:
        raise ValueError("Query and texts must not be empty")
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1")

    similarities = []
    for i, text in enumerate(texts):
        try:
            score = calculate_text_similarity(query, text, method)
            if score >= threshold:
                similarities.append((i, score))
        except ValueError:
            continue

    # Sort by similarity score in descending order
    similarities.sort(key=lambda x: x[1], reverse=True)

    if top_k is not None:
        similarities = similarities[:top_k]

    return similarities


def _tfidf_similarity(text1: str, text2: str) -> float:
    """Calculate TF-IDF based cosine similarity.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1
    """
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception as e:
        raise ValueError(f"Failed to calculate TF-IDF similarity: {str(e)}") from e


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between texts.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1
    """
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0
