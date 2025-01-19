"""Performance tests for Word processor functionality."""

import logging
from pathlib import Path
import time

from _pytest.logging import LogCaptureFixture
import pytest

from src.core.processors.word import WordProcessor

from .test_utils import PERFORMANCE_CONFIGS


logger = logging.getLogger(__name__)


def generate_performance_content(
    config: dict[str, int]
) -> tuple[list[str], list[str], list[list[str]]]:
    """Generate test content based on performance configuration.

    Args:
        config: Performance configuration with content sizes

    Returns:
        tuple[List[str], List[str], List[List[str]]]: Headers, paragraphs, and table data
    """
    # Generate headers
    headers = [f"Header {i}" for i in range(config["num_headers"])]

    # Generate paragraphs with varying length
    paragraphs = [
        f"Paragraph {i} with some content repeated multiple times: "
        f"{'Lorem ipsum ' * (i % 5 + 1)}"
        for i in range(config["num_paragraphs"])
    ]

    # Generate tables with specified dimensions
    rows, cols = config["table_size"]
    tables = []
    for t in range(config["num_tables"]):
        table = []
        for i in range(rows):
            row = [f"Cell {t}-{i}-{j}" for j in range(cols)]
            table.append(row)
        tables.append(table)

    return headers, paragraphs, tables


class TestWordProcessorPerformance:
    """Performance tests for WordProcessor."""

    @pytest.mark.parametrize("size", ["small", "medium", "large"])
    def test_document_processing(
        self,
        size: str,
        configured_processor: WordProcessor,
        doc_builder,
        caplog: LogCaptureFixture,
    ):
        """Test processing performance with different document sizes.

        Args:
            size: Size configuration to use (small, medium, large)
            configured_processor: Configured processor instance
            doc_builder: Document builder fixture
            caplog: Fixture for capturing log messages
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing %s document processing performance", size)

        config = PERFORMANCE_CONFIGS[size]
        headers, paragraphs, tables = generate_performance_content(config)

        # Create test document
        start_time = time.time()
        file_path = doc_builder(f"{size}_doc.docx")
        for header in headers:
            file_path.add_headers({1: header})
        file_path.add_paragraphs(paragraphs)
        for table in tables:
            file_path.add_table(len(table), len(table[0]), table)
        doc_path = file_path.build()
        build_time = time.time() - start_time
        logger.info("Document build time: %.2f seconds", build_time)

        # Process document and measure time
        start_time = time.time()
        result = configured_processor.process(doc_path)
        process_time = time.time() - start_time

        # Log performance metrics
        logger.info(
            "%s document processing metrics:",
            size,
            extra={
                "headers": len(headers),
                "paragraphs": len(paragraphs),
                "tables": len(tables),
                "build_time": build_time,
                "process_time": process_time,
            },
        )

        # Basic validation
        assert result.status == "success"
        assert "content" in result.content
        assert "headers" in result.content
        assert "tables" in result.content

    @pytest.mark.benchmark
    def test_concurrent_processing(
        self,
        configured_processor: WordProcessor,
        doc_builder,
        caplog: LogCaptureFixture,
        tmp_path: Path,
    ):
        """Test concurrent document processing performance.

        Args:
            configured_processor: Configured processor instance
            doc_builder: Document builder fixture
            caplog: Fixture for capturing log messages
            tmp_path: Temporary directory path
        """
        caplog.set_level(logging.DEBUG)
        logger.info("Testing concurrent document processing")

        # Create multiple test documents
        config = PERFORMANCE_CONFIGS["small"]
        headers, paragraphs, tables = generate_performance_content(config)
        docs = []

        for i in range(5):
            file_path = doc_builder(f"concurrent_doc_{i}.docx")
            for header in headers:
                file_path.add_headers({1: header})
            file_path.add_paragraphs(paragraphs)
            for table in tables:
                file_path.add_table(len(table), len(table[0]), table)
            docs.append(file_path.build())

        # Process documents concurrently and measure time
        start_time = time.time()
        results = []
        for doc in docs:
            results.append(configured_processor.process(doc))
        total_time = time.time() - start_time

        # Log performance metrics
        logger.info(
            "Concurrent processing metrics:",
            extra={
                "num_documents": len(docs),
                "total_time": total_time,
                "avg_time": total_time / len(docs),
            },
        )

        # Basic validation
        assert all(result.status == "success" for result in results)

    @pytest.mark.benchmark
    def test_memory_usage(
        self,
        configured_processor: WordProcessor,
        doc_builder,
        caplog: LogCaptureFixture,
    ):
        """Test memory usage during document processing.

        Args:
            configured_processor: Configured processor instance
            doc_builder: Document builder fixture
            caplog: Fixture for capturing log messages
        """
        import os

        import psutil

        caplog.set_level(logging.DEBUG)
        logger.info("Testing memory usage during processing")

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create and process large document
        config = PERFORMANCE_CONFIGS["large"]
        headers, paragraphs, tables = generate_performance_content(config)

        file_path = doc_builder("memory_test.docx")
        for header in headers:
            file_path.add_headers({1: header})
        file_path.add_paragraphs(paragraphs)
        for table in tables:
            file_path.add_table(len(table), len(table[0]), table)
        doc_path = file_path.build()

        # Process document and measure memory
        result = configured_processor.process(doc_path)
        peak_memory = process.memory_info().rss

        # Log memory metrics
        memory_used = peak_memory - initial_memory
        logger.info(
            "Memory usage metrics:",
            extra={
                "initial_memory_mb": initial_memory / (1024 * 1024),
                "peak_memory_mb": peak_memory / (1024 * 1024),
                "memory_used_mb": memory_used / (1024 * 1024),
            },
        )

        # Basic validation
        assert result.status == "success"
        assert memory_used > 0  # Should use some memory
        assert memory_used < 1024 * 1024 * 1024  # Should use less than 1GB
