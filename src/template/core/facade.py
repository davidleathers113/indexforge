"""Template system facade.

This module is responsible for:
1. Providing a unified interface to template functionality
2. Coordinating between different template services
3. Managing template system configuration
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment

from src.template.models.settings import TemplateSettings
from src.template.services.context import ContextService
from src.template.services.environment import EnvironmentService


class TemplateFacade:
    """Facade for template system functionality.

    This class is responsible for coordinating between different
    template services and providing a simplified interface for
    template operations.
    """

    def __init__(self):
        """Initialize the template facade."""
        self._settings = TemplateSettings.create_default()
        self._environment_service = EnvironmentService(self._settings)
        self._context_service = ContextService()

    def create_environment(self, templates_dir: str | Path) -> Environment:
        """Creates a template environment.

        Args:
            templates_dir: Path to templates directory

        Returns:
            Configured Jinja2 Environment
        """
        return self._environment_service.create_environment(templates_dir)

    def get_template_context(self, template_type: str, **kwargs) -> dict[str, Any]:
        """Gets context for template rendering.

        Args:
            template_type: Type of template
            **kwargs: Additional context variables

        Returns:
            Template context dictionary
        """
        return self._context_service.get_context(template_type, **kwargs)
