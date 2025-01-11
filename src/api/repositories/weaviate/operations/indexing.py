"""Document indexing operations."""

import logging
from typing import Dict, List, Optional

from weaviate.collections import Collection
from weaviate.util import generate_uuid5

from src.api.repositories.weaviate.operations.base import BatchOperation
from src.api.repositories.weaviate.operations.states import (
    CompletionState,
    ErrorState,
    InitialState,
    ProcessingState,
)

logger = logging.getLogger(__name__)


class IndexOperation(BatchOperation):
    """Handles document indexing operations."""

    def __init__(self, collection: Collection, batch_size: Optional[int] = None):
        """Initialize indexing operation."""
        super().__init__(collection, batch_size)
        self.initial_state = InitialState()
        self.processing_state = ProcessingState()
        self.completion_state = CompletionState()
        self.error_state = ErrorState()
        self.current_state = self.initial_state

    def prepare_item(self, item: Dict) -> Dict:
        """Prepare document for indexing."""
        doc_id = generate_uuid5(item["file_path"])
        vectors = item.pop("vectors", None)

        return {"uuid": doc_id, "properties": item, "vectors": vectors}

    def validate_item(self, item: Dict) -> bool:
        """Validate document before indexing."""
        required_fields = {"file_path", "content"}
        return all(field in item for field in required_fields)

    def process_batch(self, batch: List[Dict]) -> List[Dict]:
        """Process a batch of documents."""
        try:
            # Initial state
            items = self.initial_state.process(self, batch)

            # Processing state
            results = self.processing_state.process(self, items)

            # Completion state
            return self.completion_state.process(self, results)

        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            return self.error_state.process(self, batch)
