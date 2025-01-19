"""Template environment service.

This module is responsible for:
1. Creating and configuring Jinja2 environments
2. Managing template loading and validation
3. Providing environment factory functionality
"""

import logging
from pathlib import Path
import textwrap

from jinja2 import DebugUndefined, Environment, FileSystemLoader

from src.template.models.settings import TemplateSettings


logger = logging.getLogger(__name__)


class EnvironmentService:
    """Service for managing template environments.

    This class is responsible for creating and configuring Jinja2
    environments with the appropriate settings and template loaders.
    """

    def __init__(self, settings: TemplateSettings):
        """Initialize the environment service.

        Args:
            settings: Template engine configuration settings
        """
        self._settings = settings
        self._logger = logging.getLogger(__name__)

    def create_environment(self, templates_dir: str | Path) -> Environment:
        """Creates a new Jinja2 environment.

        This method is responsible for:
        1. Validating the template directory
        2. Setting up the template loader
        3. Configuring the environment with settings
        4. Adding custom filters and globals

        Args:
            templates_dir: Path to the templates directory

        Returns:
            Configured Jinja2 Environment

        Raises:
            ValueError: If templates directory doesn't exist
        """
        # Convert to Path object
        path = Path(templates_dir)
        self._logger.debug("Creating environment with templates dir: %s", path)

        # Validate directory exists
        self._validate_directory(path)

        # Create template loader
        loader = self._create_loader(path)
        self._logger.debug("Created template loader for path: %s", path)

        # Create environment with all settings and debug undefined
        settings_dict = self._settings.to_dict()
        settings_dict.update(
            {
                "undefined": DebugUndefined,
                "keep_trailing_newline": True,
                "trim_blocks": True,
                "lstrip_blocks": True,
                "newline_sequence": "\n",
            }
        )
        env = Environment(loader=loader, **settings_dict)
        self._logger.debug("Created Jinja2 environment with settings: %s", settings_dict)

        # Add custom filters for indentation handling
        env.filters["indent"] = self._indent_filter
        self._logger.debug("Added custom indent filter to environment")

        # Enable exports for macros
        env.globals["exports"] = []
        self._logger.debug("Enabled macro exports in environment")

        return env

    def _validate_directory(self, path: Path) -> None:
        """Validates that a template directory exists.

        Args:
            path: Directory path to validate

        Raises:
            ValueError: If directory doesn't exist
        """
        self._logger.debug("Validating template directory: %s", path)
        if not path.exists():
            msg = f"Templates directory does not exist: {path}"
            self._logger.error(msg)
            raise ValueError(msg)
        if not path.is_dir():
            msg = f"Templates path is not a directory: {path}"
            self._logger.error(msg)
            raise ValueError(msg)
        self._logger.debug("Template directory validation successful")

    def _create_loader(self, path: Path) -> FileSystemLoader:
        """Creates a template loader for the given directory.

        Args:
            path: Template directory path

        Returns:
            Configured FileSystemLoader
        """
        self._logger.debug("Creating FileSystemLoader for path: %s", path)
        return FileSystemLoader(str(path))

    def _indent_filter(self, text: str, width: int = 4, first: bool = False) -> str:
        """Custom indentation filter for Jinja2.

        This filter is responsible for:
        1. Properly indenting multiline text
        2. Handling first line indentation
        3. Preserving empty lines
        4. Maintaining consistent indentation
        5. Handling decorators and nested structures

        Args:
            text: Text to indent
            width: Number of spaces to indent
            first: Whether to indent the first line

        Returns:
            Indented text with proper formatting
        """
        if not text:
            return ""

        self._logger.debug("Indenting text with width=%d, first=%s", width, first)
        self._logger.debug("Input text:\n%s", text)

        # Dedent first to normalize indentation
        text = textwrap.dedent(text)

        # Split into lines and process
        lines = text.split("\n")
        if not lines:
            return ""

        # Calculate base indentation
        indent = " " * width

        # Process each line
        result = []
        indent_level = 0
        in_decorator = False
        in_context_setup = False

        for i, line in enumerate(lines):
            stripped = line.rstrip()

            # Handle empty lines
            if not stripped:
                result.append("")
                continue

            # Check if this is a decorator line
            is_decorator = stripped.startswith("@")
            if is_decorator:
                in_decorator = True

            # Check for context manager setup
            if "context.__" in stripped:
                in_context_setup = True
                # Context setup should be on its own line at current indent level
                result.append(indent * indent_level + stripped)
                continue

            # Check for lines that increase indent level
            if stripped.endswith(":") and not stripped.startswith(
                ("try:", "except:", "finally:", "else:")
            ):
                # Add line then increase indent
                current_indent = indent * indent_level
                result.append(current_indent + stripped if (i > 0 or first) else stripped)
                indent_level += 1
                continue

            # Check for lines that should align with their parent block
            is_aligned_with_parent = stripped.startswith(
                ("except ", "except:", "else:", "elif ", "finally:", "with ")
            ) or (in_decorator and is_decorator)

            # Calculate current line's indentation
            if is_aligned_with_parent and indent_level > 0:
                current_indent = indent * (indent_level - 1)
            else:
                current_indent = indent * indent_level

            # Add the line with appropriate indentation
            if i > 0 or first:
                result.append(current_indent + stripped)
            else:
                result.append(stripped)

            # Reset context setup flag
            if in_context_setup and "context.__" not in stripped:
                in_context_setup = False

            # Reset decorator flag if this line defines a function
            if stripped.startswith("def "):
                in_decorator = False
                indent_level += 1
            # Handle explicit indent decreasing tokens
            elif stripped.startswith(("return ", "break", "continue", "pass", "raise ")):
                if indent_level > 0:
                    indent_level -= 1

        # Join lines and ensure exactly one trailing newline
        final_text = "\n".join(result)
        self._logger.debug("Output text:\n%s", final_text)
        return final_text
