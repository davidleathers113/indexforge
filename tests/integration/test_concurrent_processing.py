"""Integration tests for concurrent document processing.

Tests the behavior of processors when handling multiple files concurrently
and validates thread safety of shared resources.
"""

import asyncio
from pathlib import Path
from typing import List

import pytest
from pytest_asyncio import fixture

from src.ml.pipeline import ExcelProcessor, PipelineConfig, TextProcessor, WordProcessor


@fixture
async def processors(pipeline_config: PipelineConfig):
    """Create and initialize processors for testing.

    Args:
        pipeline_config: Shared pipeline configuration

    Yields:
        List of initialized processors
    """
    processors = [
        TextProcessor(config=pipeline_config),
        ExcelProcessor(config=pipeline_config),
        WordProcessor(config=pipeline_config),
    ]

    for processor in processors:
        processor.initialize()

    yield processors

    for processor in processors:
        processor.cleanup()


@pytest.mark.asyncio
async def test_concurrent_initialization(pipeline_config: PipelineConfig):
    """Test concurrent initialization of multiple processors."""

    async def init_processor(processor_class):
        processor = processor_class(config=pipeline_config)
        processor.initialize()
        return processor.is_initialized

    processor_classes = [TextProcessor, ExcelProcessor, WordProcessor]
    tasks = [init_processor(cls) for cls in processor_classes]

    results = await asyncio.gather(*tasks)
    assert all(results)


@pytest.mark.asyncio
async def test_concurrent_processing(
    sample_files: dict[str, Path], processors: List[TextProcessor | ExcelProcessor | WordProcessor]
):
    """Test concurrent processing of multiple files."""

    async def process_file(processor, file_path: Path):
        return processor.process(file_path)

    tasks = []
    for processor, file_path in zip(processors, sample_files.values()):
        tasks.append(process_file(processor, file_path))

    results = await asyncio.gather(*tasks)
    assert all("content" in result for result in results)
    assert all("metadata" in result for result in results)


@pytest.mark.asyncio
async def test_concurrent_cleanup(processors: List[TextProcessor | ExcelProcessor | WordProcessor]):
    """Test concurrent cleanup of multiple processors."""

    async def cleanup_processor(processor):
        processor.cleanup()
        return processor.is_initialized

    tasks = [cleanup_processor(processor) for processor in processors]
    results = await asyncio.gather(*tasks)

    assert not any(results)
    assert all(len(processor.processed_files) == 0 for processor in processors)


@pytest.mark.asyncio
async def test_error_handling_concurrent(
    sample_files: dict[str, Path], processors: List[TextProcessor | ExcelProcessor | WordProcessor]
):
    """Test error handling during concurrent processing."""

    async def process_with_error(processor, file_path: Path):
        try:
            return await asyncio.to_thread(processor.process, file_path)
        except Exception as e:
            return e

    # Create invalid file paths
    invalid_paths = [Path(f"invalid_{i}.txt") for i in range(len(processors))]

    tasks = [process_with_error(p, f) for p, f in zip(processors, invalid_paths)]
    results = await asyncio.gather(*tasks)

    assert all(isinstance(result, ValueError) for result in results)
    assert all("File not found" in str(result) for result in results)
