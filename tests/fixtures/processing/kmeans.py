"""KMeans clustering fixtures."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from unittest.mock import MagicMock

import numpy as np
import pytest

from ..core.base import BaseState

logger = logging.getLogger(__name__)


@dataclass
class KMeansState(BaseState):
    """KMeans clustering state."""

    n_clusters: int = 3
    random_state: int = 42
    max_iter: int = 100
    error_mode: bool = False
    labels: Optional[np.ndarray] = None

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.n_clusters = 3
        self.random_state = 42
        self.max_iter = 100
        self.error_mode = False
        self.labels = None


@pytest.fixture(scope="function")
def kmeans_state():
    """Shared KMeans clustering state."""
    state = KMeansState()
    yield state
    state.reset()


@pytest.fixture(scope="function")
def mock_kmeans(kmeans_state):
    """Mock KMeans clusterer for testing."""
    mock_clusterer = MagicMock()

    def mock_fit_predict(X: np.ndarray) -> np.ndarray:
        """Simulate KMeans clustering."""
        try:
            if kmeans_state.error_mode:
                kmeans_state.add_error("KMeans clustering failed in error mode")
                raise ValueError("KMeans clustering failed in error mode")

            if len(X) < kmeans_state.n_clusters:
                kmeans_state.add_error("Not enough samples for clustering")
                raise ValueError("Not enough samples for clustering")

            # Simple deterministic clustering based on data ranges
            n_samples = len(X)
            chunk_size = n_samples // kmeans_state.n_clusters
            kmeans_state.labels = np.zeros(n_samples, dtype=int)

            for i in range(kmeans_state.n_clusters - 1):
                kmeans_state.labels[i * chunk_size : (i + 1) * chunk_size] = i
            kmeans_state.labels[(kmeans_state.n_clusters - 1) * chunk_size :] = (
                kmeans_state.n_clusters - 1
            )

            return kmeans_state.labels.copy()

        except Exception as e:
            kmeans_state.add_error(str(e))
            raise

    def mock_fit(X: np.ndarray):
        """Simulate fitting the KMeans model."""
        try:
            mock_fit_predict(X)
            return mock_clusterer
        except Exception as e:
            kmeans_state.add_error(str(e))
            raise

    def mock_predict(X: np.ndarray) -> np.ndarray:
        """Simulate predictions after fitting."""
        if kmeans_state.labels is None:
            kmeans_state.add_error("Model not fitted")
            raise ValueError("Model not fitted")
        return kmeans_state.labels.copy()

    # Configure mock methods
    mock_clusterer.fit_predict = MagicMock(side_effect=mock_fit_predict)
    mock_clusterer.fit = MagicMock(side_effect=mock_fit)
    mock_clusterer.predict = MagicMock(side_effect=mock_predict)
    mock_clusterer.get_errors = kmeans_state.get_errors
    mock_clusterer.reset = kmeans_state.reset
    mock_clusterer.set_error_mode = lambda enabled=True: setattr(
        kmeans_state, "error_mode", enabled
    )

    # Configure attributes
    mock_clusterer.n_clusters = kmeans_state.n_clusters
    mock_clusterer.random_state = kmeans_state.random_state
    mock_clusterer.max_iter = kmeans_state.max_iter

    yield mock_clusterer
    kmeans_state.reset()
