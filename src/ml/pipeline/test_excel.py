"""Tests for Excel document processor."""

from pathlib import Path

import pandas as pd
import pytest

from .config.settings import PipelineConfig
from .excel import ExcelProcessingConfig, ExcelProcessor


@pytest.fixture
def sample_excel(tmp_path: Path) -> Path:
    """Create a sample Excel file for testing.

    Args:
        tmp_path: Pytest fixture providing temporary directory path

    Returns:
        Path to the created Excel file
    """
    file_path = tmp_path / "test.xlsx"

    # Create test data
    df1 = pd.DataFrame({"Name": ["John", "Jane"], "Age": [30, 25], "City": ["New York", "London"]})

    df2 = pd.DataFrame(
        {"Product": ["Widget", "Gadget"], "Price": [99.99, 149.99], "Stock": [100, 50]}
    )

    # Create Excel file with multiple sheets
    with pd.ExcelWriter(file_path) as writer:
        df1.to_excel(writer, sheet_name="People", index=False)
        df2.to_excel(writer, sheet_name="Products", index=False)

    return file_path


def test_default_initialization():
    """Test Excel processor initialization with default config."""
    processor = ExcelProcessor()
    assert isinstance(processor.config, PipelineConfig)
    assert isinstance(processor.processing_config, ExcelProcessingConfig)
    assert not processor.is_initialized
    assert len(processor.processed_files) == 0


def test_custom_config():
    """Test Excel processor with custom configuration."""
    config = ExcelProcessingConfig(
        sheet_names=["Sheet1"], header_row=1, skip_empty=False, max_sheet_size=500
    )
    processor = ExcelProcessor(processing_config=config)
    assert processor.processing_config.sheet_names == ["Sheet1"]
    assert processor.processing_config.header_row == 1
    assert not processor.processing_config.skip_empty
    assert processor.processing_config.max_sheet_size == 500


def test_process_excel_file(sample_excel: Path):
    """Test processing of a valid Excel file."""
    processor = ExcelProcessor()

    with processor:
        result = processor.process(sample_excel)

    assert isinstance(result, dict)
    assert "content" in result
    assert "metadata" in result
    assert "sheets" in result

    # Check metadata
    assert result["metadata"]["file_path"] == str(sample_excel)
    assert result["metadata"]["file_type"] == ".xlsx"
    assert result["metadata"]["total_sheets"] == 2
    assert set(result["metadata"]["processed_sheets"]) == {"People", "Products"}

    # Check sheets
    assert len(result["sheets"]) == 2
    people_sheet = next(s for s in result["sheets"] if s["name"] == "People")
    assert people_sheet["row_count"] == 2
    assert people_sheet["column_count"] == 3

    # Check processed files tracking
    assert sample_excel in processor.processed_files


def test_process_specific_sheets(sample_excel: Path):
    """Test processing specific sheets from an Excel file."""
    config = ExcelProcessingConfig(sheet_names=["People"])
    processor = ExcelProcessor(processing_config=config)

    with processor:
        result = processor.process(sample_excel)

    assert result["metadata"]["total_sheets"] == 1
    assert result["metadata"]["processed_sheets"] == ["People"]
    assert len(result["sheets"]) == 1
    assert result["sheets"][0]["name"] == "People"


def test_invalid_file_path():
    """Test processing with invalid file path."""
    processor = ExcelProcessor()
    with processor:
        with pytest.raises(ValueError, match="File not found"):
            processor.process(Path("nonexistent.xlsx"))


def test_invalid_file_type(tmp_path: Path):
    """Test processing with invalid file type."""
    invalid_file = tmp_path / "test.txt"
    invalid_file.touch()

    processor = ExcelProcessor()
    with processor:
        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.process(invalid_file)


def test_sheet_size_limit(sample_excel: Path):
    """Test sheet size limit enforcement."""
    config = ExcelProcessingConfig(max_sheet_size=1)  # Unrealistically small
    processor = ExcelProcessor(processing_config=config)

    with processor:
        with pytest.raises(ValueError, match="exceeds maximum size"):
            processor.process(sample_excel)


def test_cleanup():
    """Test cleanup of processor resources."""
    processor = ExcelProcessor()
    processor._processed_files.add(Path("test.xlsx"))

    processor.cleanup()
    assert len(processor.processed_files) == 0
    assert not processor.is_initialized
