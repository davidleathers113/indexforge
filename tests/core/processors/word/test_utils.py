"""Test utilities and configurations for Word processor tests."""

from dataclasses import dataclass
from typing import Any


@dataclass
class TestContent:
    """Test content configurations."""

    headers: dict[int, str]
    paragraphs: list[str]
    table_data: list[list[str]]


class TestDataConfig:
    """Configuration for test data generation."""

    # Standard test content
    BASIC = TestContent(
        headers={1: "Heading 1", 2: "Heading 2", 3: "Heading 3"},
        paragraphs=[
            "First paragraph with some content.",
            "Second paragraph with different content.",
        ],
        table_data=[["Header 1", "Header 2"], ["Data 1", "Data 2"]],
    )

    # Minimal test content
    MINIMAL = TestContent(
        headers={1: "Simple Heading"},
        paragraphs=["Single paragraph."],
        table_data=[["Single Cell"]],
    )

    # Complex test content with special characters and formatting
    COMPLEX = TestContent(
        headers={
            1: "Multi-line\nHeading",
            2: "Heading with special chars: @#$%",
            3: "  Padded Heading  ",
        },
        paragraphs=[
            "Paragraph with\nmultiple\nlines",
            "Paragraph with special chars: @#$%",
            "  Paragraph with padding  ",
            "",  # Empty paragraph
        ],
        table_data=[
            ["Cell with\nnewlines", "Cell with special chars: @#$%"],
            ["  Padded cell  ", ""],  # Empty cell
        ],
    )

    @classmethod
    def get_test_config(cls, config_type: str = "basic") -> TestContent:
        """Get predefined test configuration.

        Args:
            config_type: Type of configuration to retrieve (basic, minimal, complex)

        Returns:
            TestContent: Configured test content

        Raises:
            ValueError: If config_type is not recognized
        """
        config_map = {
            "basic": cls.BASIC,
            "minimal": cls.MINIMAL,
            "complex": cls.COMPLEX,
        }
        if config_type not in config_map:
            raise ValueError(f"Unknown config type: {config_type}")
        return config_map[config_type]


class ProcessorConfig:
    """Configuration presets for Word processor."""

    # Standard configurations for different test scenarios
    CONFIGS = {
        "default": {},
        "full_extraction": {
            "extract_headers": True,
            "extract_tables": True,
            "extract_images": True,
        },
        "headers_only": {
            "extract_headers": True,
            "extract_tables": False,
            "extract_images": False,
        },
        "tables_only": {
            "extract_headers": False,
            "extract_tables": True,
            "extract_images": False,
        },
        "invalid": {
            "extract_headers": "invalid",
            "extract_tables": None,
        },
    }

    @classmethod
    def get_config(cls, config_type: str) -> dict[str, Any]:
        """Get predefined processor configuration.

        Args:
            config_type: Type of configuration to retrieve

        Returns:
            Dict[str, Any]: Processor configuration

        Raises:
            ValueError: If config_type is not recognized
        """
        if config_type not in cls.CONFIGS:
            raise ValueError(f"Unknown configuration type: {config_type}")
        return cls.CONFIGS[config_type].copy()  # Return copy to prevent modification


# Performance test configurations
PERFORMANCE_CONFIGS = {
    "small": {
        "num_headers": 5,
        "num_paragraphs": 10,
        "num_tables": 2,
        "table_size": (3, 3),
    },
    "medium": {
        "num_headers": 20,
        "num_paragraphs": 50,
        "num_tables": 5,
        "table_size": (5, 5),
    },
    "large": {
        "num_headers": 50,
        "num_paragraphs": 200,
        "num_tables": 10,
        "table_size": (10, 10),
    },
}
