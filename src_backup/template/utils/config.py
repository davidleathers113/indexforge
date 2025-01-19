"""Configuration settings for code cleanup utility."""

from dataclasses import dataclass
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Use absolute import instead of relative
from src.template.utils.logging_config import LogConfig, LogLevel


# Load environment variables
load_dotenv()


@dataclass
class TemplateConfig:
    """Template processing configuration."""

    trim_blocks: bool = True
    lstrip_blocks: bool = True
    keep_trailing_newline: bool = True
    enable_async: bool = True
    encoding: str = "utf-8"
    newline_sequence: str = "\n"
    template_dirs: set[Path] = None

    def __post_init__(self):
        """Initialize template directories set."""
        if self.template_dirs is None:
            self.template_dirs = set()

    def validate(self) -> None:
        """Validate template configuration."""
        if not isinstance(self.trim_blocks, bool):
            raise ValueError("trim_blocks must be a boolean")
        if not isinstance(self.lstrip_blocks, bool):
            raise ValueError("lstrip_blocks must be a boolean")
        if not isinstance(self.keep_trailing_newline, bool):
            raise ValueError("keep_trailing_newline must be a boolean")
        if not isinstance(self.enable_async, bool):
            raise ValueError("enable_async must be a boolean")
        if not isinstance(self.encoding, str):
            raise ValueError("encoding must be a string")
        if not isinstance(self.newline_sequence, str):
            raise ValueError("newline_sequence must be a string")
        if not isinstance(self.template_dirs, set):
            raise ValueError("template_dirs must be a set")
        for path in self.template_dirs:
            if not isinstance(path, Path):
                raise ValueError("template_dirs must contain Path objects")
            if not path.exists():
                logging.warning(f"Template directory does not exist: {path}")


@dataclass
class BlackConfig:
    """Black formatter configuration."""

    line_length: int = 88
    target_version: str = "py37"
    string_normalization: bool = True
    is_pyi: bool = False

    def validate(self) -> None:
        """Validate black configuration."""
        if not isinstance(self.line_length, int) or self.line_length < 1:
            raise ValueError("line_length must be a positive integer")
        if not isinstance(self.target_version, str):
            raise ValueError("target_version must be a string")
        if not isinstance(self.string_normalization, bool):
            raise ValueError("string_normalization must be a boolean")
        if not isinstance(self.is_pyi, bool):
            raise ValueError("is_pyi must be a boolean")


@dataclass
class IsortConfig:
    """Import sorter configuration."""

    profile: str = "black"
    line_length: int = 88
    multi_line_output: int = 3
    include_trailing_comma: bool = True
    force_grid_wrap: int = 0
    use_parentheses: bool = True
    ensure_newline_before_comments: bool = True

    def validate(self) -> None:
        """Validate isort configuration."""
        if not isinstance(self.profile, str):
            raise ValueError("profile must be a string")
        if not isinstance(self.line_length, int) or self.line_length < 1:
            raise ValueError("line_length must be a positive integer")
        if not isinstance(self.multi_line_output, int) or self.multi_line_output not in range(7):
            raise ValueError("multi_line_output must be an integer between 0 and 6")
        if not isinstance(self.include_trailing_comma, bool):
            raise ValueError("include_trailing_comma must be a boolean")
        if not isinstance(self.force_grid_wrap, int) or self.force_grid_wrap < 0:
            raise ValueError("force_grid_wrap must be a non-negative integer")
        if not isinstance(self.use_parentheses, bool):
            raise ValueError("use_parentheses must be a boolean")
        if not isinstance(self.ensure_newline_before_comments, bool):
            raise ValueError("ensure_newline_before_comments must be a boolean")


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""

    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1

    def validate(self) -> None:
        """Validate OpenAI configuration."""
        if not isinstance(self.api_key, str):
            raise ValueError("api_key must be a string")
        if not self.api_key and os.environ.get("OPENAI_API_KEY") is None:
            logging.warning("OpenAI API key not found in environment variables")
        if not isinstance(self.model, str):
            raise ValueError("model must be a string")
        if not isinstance(self.temperature, (int, float)) or not 0 <= self.temperature <= 1:
            raise ValueError("temperature must be a float between 0 and 1")
        if not isinstance(self.max_tokens, int) or self.max_tokens < 1:
            raise ValueError("max_tokens must be a positive integer")
        if not isinstance(self.request_timeout, int) or self.request_timeout < 1:
            raise ValueError("request_timeout must be a positive integer")
        if not isinstance(self.max_retries, int) or self.max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        if not isinstance(self.retry_delay, int) or self.retry_delay < 0:
            raise ValueError("retry_delay must be a non-negative integer")


class Config:
    """Central configuration class for code cleanup utility."""

    def __init__(
        self,
        python_indent: int = 4,
        black_config: BlackConfig | None = None,
        isort_config: dict | None = None,
        openai_config: OpenAIConfig | None = None,
        template_config: TemplateConfig | None = None,
        log_config: LogConfig | None = None,
        dry_run: bool = False,
    ):
        """Initialize configuration with default values."""
        self.PYTHON_INDENT = python_indent
        self.BLACK_CONFIG = black_config or BlackConfig()
        self.ISORT_CONFIG = isort_config or IsortConfig().__dict__
        self.OPENAI_CONFIG = openai_config or OpenAIConfig()
        self.TEMPLATE_CONFIG = template_config or TemplateConfig()
        self.LOG_CONFIG = log_config or LogConfig()
        self.DRY_RUN = dry_run
        self.validate()

    def validate(self) -> None:
        """Validate all configuration settings."""
        if not isinstance(self.PYTHON_INDENT, int) or self.PYTHON_INDENT < 1:
            raise ValueError("PYTHON_INDENT must be a positive integer")

        if not isinstance(self.DRY_RUN, bool):
            raise ValueError("DRY_RUN must be a boolean")

        # Validate component configs
        self.BLACK_CONFIG.validate()
        IsortConfig(**self.ISORT_CONFIG).validate()
        self.OPENAI_CONFIG.validate()
        self.TEMPLATE_CONFIG.validate()

        # Ensure log config is valid
        if not isinstance(self.LOG_CONFIG, LogConfig):
            raise ValueError("LOG_CONFIG must be a LogConfig instance")
        if not isinstance(self.LOG_CONFIG.level, LogLevel):
            raise ValueError("LOG_CONFIG.level must be a LogLevel enum value")
        if self.LOG_CONFIG.file_path and not isinstance(self.LOG_CONFIG.file_path, (str, Path)):
            raise ValueError("LOG_CONFIG.file_path must be a string or Path")

        # Check for conflicting settings
        if self.BLACK_CONFIG.line_length != self.ISORT_CONFIG["line_length"]:
            logging.warning("Black and isort line length settings differ")
