"""Processor classes for code cleanup utility."""

import ast
from dataclasses import dataclass
import logging
from pathlib import Path

from openai import OpenAI


logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """Result of a processing operation."""

    success: bool
    content: str
    error: str | None = None


def validate_python_syntax(content: str) -> str | None:
    """Validate Python syntax.

    Args:
        content: Python code content to validate

    Returns:
        Optional[str]: Error message if validation fails, None if successful
    """
    try:
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"Syntax error at line {e.lineno}, offset {e.offset}: {e.msg}"
    except Exception as e:
        return f"Validation error: {e!s}"


class TemplateDetector:
    """Detects if a file is a template file."""

    def is_template_file(self, content: str) -> bool:
        """Check if content contains template markers.

        Args:
            content: File content to check

        Returns:
            bool: True if content contains template markers
        """
        return any(
            marker in content
            for marker in [
                "context = mocker.Mock()",
                "setup_context_manager",
                "{%",
                "{{",
                "dedent(",
            ]
        )


class AIProcessor:
    """Handles AI-powered code improvements."""

    def __init__(self, config: dict):
        """Initialize with OpenAI configuration.

        Args:
            config: OpenAI configuration settings
        """
        self.config = config
        self.client = OpenAI(api_key=config.api_key) if config.api_key else None

    def process(self, content: str) -> ProcessResult:
        """Process content using AI.

        Args:
            content: Content to process

        Returns:
            ProcessResult: Result of processing
        """
        if not self.client:
            return ProcessResult(
                success=False, content=content, error="OpenAI client not initialized"
            )

        try:
            prompt = f"""As a Python code improvement assistant, analyze and improve the following code that has already undergone basic formatting.
            Focus on:
            1. Logical errors and edge cases
            2. Code clarity and maintainability
            3. Performance optimizations
            4. Documentation completeness
            5. Pythonic idioms and best practices

            Provide the improved code followed by a brief explanation of changes.
            If no improvements are needed, respond with "NO_CHANGES_NEEDED".

            Code to analyze:
            ```python
            {content}
            ```"""

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a Python code improvement assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            ai_response = response.choices[0].message.content.strip()

            if ai_response == "NO_CHANGES_NEEDED":
                return ProcessResult(success=True, content=content)

            if "```python" in ai_response:
                parts = ai_response.split("```python")
                if len(parts) > 1:
                    code_parts = parts[1].split("```")
                    if code_parts:
                        improved_code = code_parts[0].strip()
                        return ProcessResult(success=True, content=improved_code)

            return ProcessResult(
                success=False, content=content, error="Could not parse AI response"
            )

        except Exception as e:
            return ProcessResult(
                success=False, content=content, error=f"AI processing failed: {e!s}"
            )


class FileProcessor:
    """Processes files with appropriate formatters."""

    def __init__(self, processors: dict, is_template: bool = False, use_ai: bool = False):
        """Initialize with processors and flags."""
        self.processors = processors
        self.is_template = is_template
        self.use_ai = use_ai
        logger.debug(
            "Initialized FileProcessor with template=%s, use_ai=%s, processors=%s",
            is_template,
            use_ai,
            list(processors.keys()),
        )

    def process(self, filepath: Path, content: str) -> ProcessResult:
        """Process a file with all appropriate processors."""
        try:
            logger.info("Starting to process file: %s", filepath)
            logger.debug("Initial content:\n%s", content)

            # Always run whitespace first
            logger.debug("Running whitespace processor")
            content = self.processors["whitespace"].format(content)
            logger.debug("Content after whitespace:\n%s", content)

            if self.is_template:
                # For templates, only run indentation and statement splitting
                logger.debug("Processing template file")
                content = self.processors["indentation"].format(content)
                content = self.processors["statements"].format(content)
            else:
                # For regular files, run all processors
                logger.debug("Processing regular file")
                content = self.processors["indentation"].format(content)
                content = self.processors["statements"].format(content)
                content = self.processors["imports"].format(content)

                # Run AI processor if enabled
                if self.use_ai:
                    logger.debug("Running AI processor")
                    result = self.processors["ai"].process(content)
                    if result.success:
                        content = result.content
                        logger.debug("Content after AI processing:\n%s", content)
                    else:
                        logger.warning("AI processing failed: %s", result.error)

                # Run black last
                content = self.processors["black"].format(content)

            # Validate final content
            error = validate_python_syntax(content)
            if error:
                logger.error("Validation failed: %s", error)
                return ProcessResult(success=False, content=content, error=error)

            logger.info("Processing completed successfully")
            return ProcessResult(success=True, content=content)

        except Exception as e:
            error_msg = f"Processing failed: {e!s}"
            logger.error(error_msg, exc_info=True)
            return ProcessResult(success=False, content=content, error=error_msg)
