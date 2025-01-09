"""Template settings model.

This module is responsible for:
1. Defining the template engine configuration settings
2. Providing type-safe access to template settings
3. Ensuring consistent template behavior across the application
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TemplateSettings:
    """Template engine configuration settings.

    This class is responsible for storing and providing access to all
    Jinja2 template engine configuration parameters needed for proper
    Python code generation and indentation handling.

    Attributes:
        block_start_string: Start delimiter for template blocks ({%)
        block_end_string: End delimiter for template blocks (%})
        variable_start_string: Start delimiter for variables ({{)
        variable_end_string: End delimiter for variables (}})
        comment_start_string: Start delimiter for comments ({#)
        comment_end_string: End delimiter for comments (#})
        line_statement_prefix: Prefix for line-based statements (None)
        line_comment_prefix: Prefix for line-based comments (None)
        trim_blocks: Whether to trim first newline after blocks (True)
        lstrip_blocks: Whether to strip whitespace before blocks (True)
        newline_sequence: Character(s) to use for newlines (\n)
        keep_trailing_newline: Whether to keep trailing newlines (True)
        autoescape: Whether to enable autoescaping (False)
        enable_async: Whether to enable macro exports (True)
    """

    # Block delimiters
    block_start_string: str = "{%"
    block_end_string: str = "%}"
    variable_start_string: str = "{{"
    variable_end_string: str = "}}"
    comment_start_string: str = "{#"
    comment_end_string: str = "#}"

    # Line handling
    line_statement_prefix: Optional[str] = None
    line_comment_prefix: Optional[str] = None
    trim_blocks: bool = True
    lstrip_blocks: bool = True

    # Newline handling
    newline_sequence: str = "\n"
    keep_trailing_newline: bool = True

    # Escaping
    autoescape: bool = False

    # Enable macro exports
    enable_async: bool = True

    @classmethod
    def create_default(cls) -> "TemplateSettings":
        """Creates a TemplateSettings instance with default values.

        This method is responsible for creating a new instance with all
        attributes initialized to their default values, which are optimized
        for Python code generation.

        Returns:
            A TemplateSettings instance configured with default values
            suitable for Python code generation.
        """
        return cls(
            # Block delimiters - use standard Jinja2 delimiters
            block_start_string="{%",
            block_end_string="%}",
            variable_start_string="{{",
            variable_end_string="}}",
            comment_start_string="{#",
            comment_end_string="#}",
            # Line handling - optimize for Python code
            line_statement_prefix=None,  # Don't use line statements
            line_comment_prefix=None,  # Don't use line comments
            trim_blocks=True,  # Remove first newline after blocks
            lstrip_blocks=True,  # Strip whitespace before blocks
            # Newline handling - critical for Python
            newline_sequence="\n",  # Use Unix-style newlines
            keep_trailing_newline=True,  # Keep trailing newlines
            # Escaping - not needed for Python code
            autoescape=False,
            # Enable macro exports
            enable_async=True,  # Required for some macro features
        )

    def to_dict(self) -> dict:
        """Converts settings to a dictionary for Jinja2 configuration.

        This method is responsible for converting all settings into a format
        that can be used to initialize a Jinja2 Environment instance.

        Returns:
            Dictionary of settings suitable for Jinja2 Environment initialization.
        """
        return {
            # Block delimiters
            "block_start_string": self.block_start_string,
            "block_end_string": self.block_end_string,
            "variable_start_string": self.variable_start_string,
            "variable_end_string": self.variable_end_string,
            "comment_start_string": self.comment_start_string,
            "comment_end_string": self.comment_end_string,
            # Line handling
            "line_statement_prefix": self.line_statement_prefix,
            "line_comment_prefix": self.line_comment_prefix,
            "trim_blocks": self.trim_blocks,
            "lstrip_blocks": self.lstrip_blocks,
            # Newline handling
            "newline_sequence": self.newline_sequence,
            "keep_trailing_newline": self.keep_trailing_newline,
            # Escaping
            "autoescape": self.autoescape,
            # Enable macro exports
            "enable_async": self.enable_async,
        }
