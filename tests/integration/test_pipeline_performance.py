"""Integration tests for pipeline performance.

Tests the performance characteristics of the document processing pipeline,
including throughput, resource usage, and scaling behavior.
"""

import time
from pathlib import Path
from typing import List

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from src.ml.pipeline import ExcelProcessor, PipelineConfig, TextProcessor, WordProcessor


@pytest.fixture
def large_text_files(tmp_path: Path) -> List[Path]:
    """Create a set of large text files for performance testing.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        List of paths to generated text files
    """
    files = []
    content = "Sample content\n" * 1000  # ~14KB per file

    for i in range(10):
        file_path = tmp_path / f"large_file_{i}.txt"
        file_path.write_text(content)
        files.append(file_path)

    return files


def test_text_processor_throughput(
    large_text_files: List[Path], pipeline_config: PipelineConfig, benchmark: BenchmarkFixture
):
    """Benchmark text processor throughput.

    Tests the processing speed and memory usage for text files.
    """

    def process_files():
        processor = TextProcessor(config=pipeline_config)
        results = []

        with processor:
            for file_path in large_text_files:
                results.append(processor.process(file_path))

        return results

    # Run benchmark
    result = benchmark(process_files)

    # Verify benchmark completed successfully
    assert result.stats["iterations"] > 0
    assert "max" in result.stats
    assert "mean" in result.stats


def test_processor_scaling(
    large_text_files: List[Path], pipeline_config: PipelineConfig, benchmark: BenchmarkFixture
):
    """Test processing performance with different batch sizes."""

    def process_batch(batch_size: int):
        config = PipelineConfig(**pipeline_config.model_dump(), batch_size=batch_size)
        processor = TextProcessor(config=config)

        with processor:
            start_time = time.time()
            for file_path in large_text_files[:batch_size]:
                processor.process(file_path)
            end_time = time.time()

        return end_time - start_time

    # Test different batch sizes
    batch_sizes = [1, 2, 5, 10]
    times = [process_batch(size) for size in batch_sizes]

    # Verify processing time scales reasonably with batch size
    for i in range(1, len(times)):
        # Time per file should not increase significantly with batch size
        time_per_file_current = times[i] / batch_sizes[i]
        time_per_file_previous = times[i - 1] / batch_sizes[i - 1]

        assert time_per_file_current <= time_per_file_previous * 1.5


def test_memory_usage(large_text_files: List[Path], pipeline_config: PipelineConfig):
    """Test memory usage during processing."""
    import os

    import psutil

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    processor = TextProcessor(config=pipeline_config)
    with processor:
        # Process files and check memory after each
        for i, file_path in enumerate(large_text_files, 1):
            processor.process(file_path)

            # Check memory usage
            current_memory = process.memory_info().rss
            memory_increase = current_memory - initial_memory

            # Memory should not grow unbounded with number of files
            # Allow for some overhead but expect reasonable scaling
            assert memory_increase <= initial_memory * (i * 0.5)


def test_concurrent_performance(
    large_text_files: List[Path], pipeline_config: PipelineConfig, benchmark: BenchmarkFixture
):
    """Test performance of concurrent processing."""
    import asyncio

    async def process_concurrent():
        processors = [TextProcessor(config=pipeline_config) for _ in range(3)]
        tasks = []

        # Initialize processors
        for processor in processors:
            processor.initialize()

        try:
            # Process files concurrently
            for i, processor in enumerate(processors):
                batch = large_text_files[i::3]  # Distribute files among processors
                tasks.extend(
                    asyncio.create_task(asyncio.to_thread(processor.process, file_path))
                    for file_path in batch
                )

            results = await asyncio.gather(*tasks)
            return results

        finally:
            # Cleanup
            for processor in processors:
                processor.cleanup()

    def run_concurrent():
        return asyncio.run(process_concurrent())

    # Run benchmark
    result = benchmark(run_concurrent)

    # Verify benchmark completed successfully
    assert result.stats["iterations"] > 0
    assert "max" in result.stats
    assert "mean" in result.stats
