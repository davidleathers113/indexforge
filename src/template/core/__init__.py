"""Template core package.

This package is responsible for:
1. Providing high-level coordination between template components
2. Exposing unified interfaces for template functionality
"""

from .facade import TemplateFacade

__all__ = ["TemplateFacade"]
