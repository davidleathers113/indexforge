"""Template package initialization.

This module is responsible for:
1. Exposing public interface
2. Initializing package components
3. Managing version information
"""

import logging
from pathlib import Path
from typing import Any, Dict, Union

from jinja2 import Environment

from .models.settings import TemplateSettings
from .services.context import ContextService
from .services.environment import EnvironmentService

__version__ = "0.1.0"

# Configure logging
logger = logging.getLogger(__name__)

# Create service instances
_context_service = ContextService()
_environment_service = EnvironmentService(TemplateSettings.create_default())


def create_environment(templates_dir: Union[str, Path]) -> Environment:
    """Creates a configured template environment.

    This function is responsible for:
    1. Creating default settings
    2. Initializing environment service
    3. Creating and configuring environment

    Args:
        templates_dir: Path to templates directory

    Returns:
        Configured Jinja2 Environment
    """
    return _environment_service.create_environment(templates_dir)


def get_template_context(template_type: str, **kwargs) -> Dict[str, Any]:
    """Gets context for template rendering.

    This function is responsible for:
    1. Validating template type
    2. Gathering context data
    3. Providing template helpers

    Args:
        template_type: Type of template
        **kwargs: Additional context variables

    Returns:
        Template context dictionary
    """
    return _context_service.get_context(template_type, **kwargs)


# Only expose the high-level functions
__all__ = ["create_environment", "get_template_context", "__version__"]
