"""Unit tests for document processing configuration.

Tests the validation and functionality of document processing configuration settings.
"""

import pytest
from pydantic import ValidationError

from src.ml.processing.document.config import (
    DocumentProcessingConfig,
    ExcelProcessingConfig,
    WordProcessingConfig,
)


def test_excel_config_defaults():
    """Test default Excel processing configuration."""
    config = ExcelProcessingConfig()
    assert config.max_rows == 0
    assert config.max_cols == 0
    assert not config.sheet_names
    assert config.header_row == 0
    assert config.skip_empty is True
    assert not config.required_columns


def test_excel_config_custom():
    """Test custom Excel processing configuration."""
    config = ExcelProcessingConfig(
        max_rows=1000,
        max_cols=50,
        sheet_names={"Sheet1", "Data"},
        header_row=1,
        skip_empty=False,
        required_columns=["ID", "Name"],
    )
    assert config.max_rows == 1000
    assert config.max_cols == 50
    assert config.sheet_names == {"Sheet1", "Data"}
    assert config.header_row == 1
    assert config.skip_empty is False
    assert config.required_columns == ["ID", "Name"]


def test_excel_config_validation():
    """Test Excel configuration validation."""
    with pytest.raises(ValidationError):
        ExcelProcessingConfig(max_rows=-1)

    with pytest.raises(ValidationError):
        ExcelProcessingConfig(max_cols=-1)

    with pytest.raises(ValidationError):
        ExcelProcessingConfig(header_row=-1)


def test_word_config_defaults():
    """Test default Word processing configuration."""
    config = WordProcessingConfig()
    assert config.extract_headers is True
    assert config.extract_tables is True
    assert config.extract_images is False
    assert config.max_image_size == 0
    assert config.preserve_formatting is False


def test_word_config_custom():
    """Test custom Word processing configuration."""
    config = WordProcessingConfig(
        extract_headers=False,
        extract_tables=False,
        extract_images=True,
        max_image_size=1000000,
        preserve_formatting=True,
    )
    assert config.extract_headers is False
    assert config.extract_tables is False
    assert config.extract_images is True
    assert config.max_image_size == 1000000
    assert config.preserve_formatting is True


def test_word_config_validation():
    """Test Word configuration validation."""
    with pytest.raises(ValidationError):
        WordProcessingConfig(max_image_size=-1)


def test_document_config_defaults():
    """Test default document processing configuration."""
    config = DocumentProcessingConfig()
    assert isinstance(config.excel_config, ExcelProcessingConfig)
    assert isinstance(config.word_config, WordProcessingConfig)
    assert config.max_file_size == 0
    assert ".xlsx" in config.supported_extensions
    assert ".docx" in config.supported_extensions
    assert config.extract_metadata is True
    assert config.validate_content is True
    assert config.chunk_size == 0


def test_document_config_custom():
    """Test custom document processing configuration."""
    excel_config = ExcelProcessingConfig(max_rows=1000)
    word_config = WordProcessingConfig(extract_images=True)

    config = DocumentProcessingConfig(
        excel_config=excel_config,
        word_config=word_config,
        max_file_size=10000000,
        supported_extensions={".xlsx", ".csv"},
        extract_metadata=False,
        validate_content=False,
        chunk_size=1000,
    )

    assert config.excel_config.max_rows == 1000
    assert config.word_config.extract_images is True
    assert config.max_file_size == 10000000
    assert config.supported_extensions == {".xlsx", ".csv"}
    assert config.extract_metadata is False
    assert config.validate_content is False
    assert config.chunk_size == 1000


def test_document_config_validation():
    """Test document configuration validation."""
    with pytest.raises(ValidationError):
        DocumentProcessingConfig(max_file_size=-1)

    with pytest.raises(ValidationError):
        DocumentProcessingConfig(chunk_size=-1)

    with pytest.raises(ValidationError):
        DocumentProcessingConfig(supported_extensions={"txt"})  # Missing dot

    with pytest.raises(ValidationError):
        DocumentProcessingConfig(supported_extensions={".txt$"})  # Invalid char


def test_config_dict_conversion():
    """Test configuration to dictionary conversion."""
    config = DocumentProcessingConfig(
        excel_config=ExcelProcessingConfig(max_rows=1000),
        word_config=WordProcessingConfig(extract_images=True),
        max_file_size=10000000,
    )

    config_dict = config.model_dump()
    assert isinstance(config_dict, dict)
    assert config_dict["excel_config"]["max_rows"] == 1000
    assert config_dict["word_config"]["extract_images"] is True
    assert config_dict["max_file_size"] == 10000000


def test_config_json_conversion():
    """Test configuration JSON serialization."""
    config = DocumentProcessingConfig()
    json_str = config.model_dump_json()
    assert isinstance(json_str, str)
    assert "excel_config" in json_str
    assert "word_config" in json_str
