"""ML service components.

This module provides service-related functionality for ML operations,
including service states, initialization, and error handling.
"""

from enum import Enum, auto
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(title="IndexForge ML Service")

# Initialize model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


class TextInput(BaseModel):
    text: str


@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/embed")
async def create_embedding(input_data: TextInput):
    try:
        # Generate embedding
        embedding = model.encode(input_data.text)
        return {"embedding": embedding.tolist(), "dimensions": len(embedding)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model-info")
async def model_info():
    return {
        "model_name": model.get_sentence_embedding_dimension(),
        "device": str(next(model.parameters()).device),
        "embedding_dimension": model.get_sentence_embedding_dimension(),
    }


class ServiceState(Enum):
    """States for ML service lifecycle."""

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    ERROR = auto()
    STOPPED = auto()


class ServiceInitializationError(Exception):
    """Raised when service initialization fails."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        cause: Optional[Exception] = None,
        missing_dependencies: Optional[list[str]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the service that failed
            cause: Original exception that caused this error
            missing_dependencies: List of missing dependencies
        """
        self.service_name = service_name
        self.cause = cause
        self.missing_dependencies = missing_dependencies or []
        super().__init__(message)


class ServiceNotInitializedError(Exception):
    """Raised when attempting to use an uninitialized service."""

    def __init__(self, message: str, service_name: Optional[str] = None) -> None:
        """Initialize the error.

        Args:
            message: Error message
            service_name: Name of the uninitialized service
        """
        self.service_name = service_name
        super().__init__(message)


# Feature flags
EMBEDDING_AVAILABLE = True  # Set based on dependencies
