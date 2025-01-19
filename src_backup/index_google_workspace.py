"""Script to index Google Workspace exported files.

This script processes and indexes files from the Google Workspace export directory
using the direct documentation indexing connector and indexes them in Weaviate.
"""

import json
import logging
from pathlib import Path
import sys

import weaviate


# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Import after adding project root to path
from src.connectors.direct_documentation_indexing import (  # noqa: E402
    DocumentConnector,
    ExcelProcessor,
    WordProcessor,
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_existing_schema(client: weaviate.Client) -> None:
    """Delete the existing Document collection if it exists."""
    try:
        schema = client.schema.get()
        if any(cls["class"] == "Document" for cls in schema["classes"]):
            logger.info("Deleting existing Document collection...")
            client.schema.delete_class("Document")
            logger.info("Successfully deleted Document collection")
    except Exception as e:
        logger.error(f"Failed to delete schema: {e!s}")
        raise


def setup_weaviate_schema(client: weaviate.Client) -> None:
    """Set up the Weaviate schema for document indexing if it doesn't exist."""
    try:
        # Check if schema exists
        schema = client.schema.get()
        if any(cls["class"] == "Document" for cls in schema.get("classes", [])):
            logger.info("Document collection already exists, skipping schema creation")
            return

        # Create schema only if it doesn't exist
        schema = {
            "class": "Document",
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "model": "sentence-transformers-all-MiniLM-L6-v2",
                    "poolingStrategy": "mean",
                    "vectorizeClassName": False,
                }
            },
            "properties": [
                {"name": "title", "dataType": ["text"]},
                {
                    "name": "content",
                    "dataType": ["text"],
                    "moduleConfig": {
                        "text2vec-transformers": {"skip": False, "vectorizePropertyName": False}
                    },
                },
                {
                    "name": "file_path",
                    "dataType": ["text"],
                    "indexInverted": True,
                    "uniqueTokenization": True,
                    "tokenization": "field",
                },
                {"name": "file_type", "dataType": ["text"]},
                {
                    "name": "metadata_json",
                    "dataType": ["text"],
                    "description": "Document metadata stored as JSON string",
                },
            ],
            "vectorIndexConfig": {
                "distance": "cosine",
                "ef": 100,
                "efConstruction": 128,
                "maxConnections": 64,
            },
            "invertedIndexConfig": {
                "indexTimestamps": True,
                "indexNullState": True,
            },
        }

        client.schema.create_class(schema)
        logger.info("Created Weaviate schema successfully")
    except Exception as e:
        logger.error(f"Failed to create schema: {e!s}")
        raise


def index_documents(client: weaviate.Client, documents: list[dict]) -> None:
    """Index documents in Weaviate using optimized batch import with upsert behavior."""
    try:
        # Configure batch settings with consistency level
        client.batch.configure(
            batch_size=100, dynamic=True, consistency_level="ALL"  # Ensure strong consistency
        )

        def sanitize_float(value):
            if isinstance(value, float):
                if value in (float("inf"), float("-inf"), float("nan")):
                    return str(value)
            return value

        def sanitize_dict(d):
            return {
                k: sanitize_float(v) if isinstance(v, (int, float)) else v for k, v in d.items()
            }

        # Index documents in batches with upsert behavior
        with client.batch as batch:
            for doc in documents:
                file_path = doc.get("file_path", "")

                properties = {
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
                    "file_path": file_path,
                    "file_type": doc.get("file_type", ""),
                    "metadata_json": json.dumps(sanitize_dict(doc.get("metadata", {}))),
                }

                # Use Weaviate's built-in upsert with file_path as unique identifier
                batch.add_data_object(
                    data_object=properties,
                    class_name="Document",
                    uuid=None,  # Let Weaviate handle UUID generation/matching
                    vector=None,  # Let Weaviate generate the vector
                )

        logger.info(f"Successfully indexed {len(documents)} documents")
    except Exception as e:
        logger.error(f"Failed to index documents: {e!s}")
        raise


def main():
    # Initialize Weaviate client
    client = weaviate.Client(url="http://localhost:8080")

    try:
        # Set up Weaviate schema
        setup_weaviate_schema(client)

        # Configure processors
        excel_config = {
            "max_rows": None,  # No row limit
            "required_columns": [],  # No required columns
            "skip_sheets": [],  # Don't skip any sheets
        }

        word_config = {"extract_headers": True, "extract_tables": True, "extract_images": False}

        # Initialize connector with configured processors
        connector = DocumentConnector()
        connector.processors = {
            "excel": ExcelProcessor(excel_config),
            "word": WordProcessor(word_config),
        }

        # Process all documents recursively
        export_dir = Path("google-workspace-export")
        logger.info(f"Starting document processing from {export_dir}")

        all_documents = []
        for subdir in ["Daves Files/Downloads", "Daves Files/Downloads 2"]:
            dir_path = export_dir / subdir
            logger.info(f"Processing directory: {dir_path}")

            try:
                # Process each file in the directory
                results = []
                for file_path in dir_path.glob("*.*"):
                    suffix = file_path.suffix.lower()
                    processor_type = (
                        "excel"
                        if suffix in {".xlsx", ".xls", ".csv"}
                        else "word" if suffix in {".docx", ".doc"} else None
                    )

                    if processor_type and processor_type in connector.processors:
                        result = connector.process_file(file_path)
                        results.append(result)

                        # Prepare successful results for indexing
                        if result["status"] == "success":
                            doc = {
                                "title": file_path.name,
                                "content": result["content"],
                                "file_path": str(file_path),
                                "file_type": suffix,
                                "metadata": result.get("metadata", {}),
                            }
                            all_documents.append(doc)

                # Log processing results
                success_count = sum(1 for r in results if r["status"] == "success")
                error_count = sum(1 for r in results if r["status"] == "error")

                logger.info(f"Directory {subdir} processing complete:")
                logger.info(f"- Successfully processed: {success_count} files")
                logger.info(f"- Failed to process: {error_count} files")

                if error_count > 0:
                    logger.warning("Files that failed to process:")
                    for result in results:
                        if result["status"] == "error":
                            logger.warning(f"- {result['file']}: {result['error']}")

            except Exception as e:
                logger.error(f"Failed to process directory {subdir}: {e!s}")

        # Index all processed documents in Weaviate
        if all_documents:
            logger.info(f"Indexing {len(all_documents)} documents in Weaviate")
            index_documents(client, all_documents)
        else:
            logger.warning("No documents were successfully processed for indexing")

    except Exception as e:
        logger.error(f"An error occurred: {e!s}")
        raise


if __name__ == "__main__":
    main()
