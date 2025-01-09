"""Template environment module.

This module is responsible for:
1. Configuring Jinja2 environments for Python code generation
2. Providing template context helpers for testing and verification
3. Managing template loading and validation
"""

import logging
from pathlib import Path
from typing import Any, Dict, Union

from jinja2 import Environment

from .models.settings import TemplateSettings
from .services.context import ContextService
from .services.environment import EnvironmentService

# Configure logging
logger = logging.getLogger(__name__)

# Create service instances
_context_service = ContextService()
_environment_service = EnvironmentService(TemplateSettings.create_default())


def create_environment(templates_dir: Union[str, Path]) -> Environment:
    """Creates a Jinja2 environment for template rendering.

    This function is responsible for:
    1. Validating the template directory
    2. Creating a FileSystemLoader
    3. Configuring the Jinja2 environment

    Example:
        >>> env = create_environment("templates")
        >>> template = env.get_template("test_cache.py.jinja")
        >>> result = template.render(function_name="test_cache_hit")

    Args:
        templates_dir: Path to the directory containing templates

    Returns:
        Configured Jinja2 Environment

    Raises:
        FileNotFoundError: If templates_dir doesn't exist or isn't a directory
    """
    return _environment_service.create_environment(templates_dir)


def get_template_context(template_type: str, **kwargs) -> Dict[str, Any]:
    """Gets context dictionary for template rendering.

    This function provides helpers for:
    1. Setting up test mocks (cache, serialization, retries)
    2. Verifying mock interactions
    3. Validating test results

    Example:
        >>> context = get_template_context("cache_test")
        >>> mock_cache = context["setup_cache_mock"]()
        >>> context["verify_cache_call"](mock_cache, "get", "key1")

    Args:
        template_type: Type of template being rendered
        **kwargs: Additional context variables

    Returns:
        Dictionary containing helper functions and context variables

    Raises:
        ValueError: If template_type is not recognized
    """
    return _context_service.get_context(template_type, **kwargs)
