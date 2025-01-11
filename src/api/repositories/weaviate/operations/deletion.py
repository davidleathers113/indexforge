"""Document deletion operations."""

import logging
from typing import Dict, List, Optional

from weaviate.collections import Collection

from src.api.repositories.weaviate.operations.base import BatchOperation
from src.api.repositories.weaviate.operations.states import (
    CompletionState,
    ErrorState,
    InitialState,
    ProcessingState,
)

logger = logging.getLogger(__name__)


class DeleteOperation(BatchOperation):
    """Handles document deletion operations."""

    def __init__(self, collection: Collection, batch_size: Optional[int] = None):
        """Initialize deletion operation."""
        super().__init__(collection, batch_size)
        self.initial_state = InitialState()
        self.processing_state = ProcessingState()
        self.completion_state = CompletionState()
        self.error_state = ErrorState()
        self.current_state = self.initial_state

    def prepare_item(self, item: Dict) -> Dict:
        """Prepare document for deletion."""
        return {"uuid": item["uuid"]} if "uuid" in item else item

    def validate_item(self, item: Dict) -> bool:
        """Validate document before deletion."""
        return "uuid" in item

    def process_batch(self, batch: List[Dict]) -> List[Dict]:
        """Process a batch of documents for deletion."""
        try:
            # Initial state
            items = self.initial_state.process(self, batch)

            # Processing state
            results = self.processing_state.process(self, items)

            # Completion state
            return self.completion_state.process(self, results)

        except Exception as e:
            logger.error(f"Batch deletion failed: {str(e)}")
            return self.error_state.process(self, batch)
