"""Alert system models.

This module provides backward compatibility for importing alert models.
It re-exports model classes from their new locations in the models package.

.. deprecated:: 1.0.0
   Import directly from src.core.monitoring.alerts.models.* instead.
   This module will be removed in version 2.0.0.

Example:
    Old import style (deprecated):
    ```python
    from src.core.monitoring.alerts.models import Alert, AlertConfig

    alert = Alert(...)
    ```

    New import style:
    ```python
    from src.core.monitoring.alerts.models.alert import Alert
    from src.core.monitoring.alerts.models.config import AlertConfig

    alert = Alert(...)
    ```
"""

import warnings

# Re-export model classes
from .models.alert import Alert
from .models.config import AlertConfig
from .models.types import AlertSeverity, AlertType

# Emit deprecation warning
warnings.warn(
    "Importing from src.core.monitoring.alerts.models is deprecated. "
    "Import directly from src.core.monitoring.alerts.models.* instead. "
    "This module will be removed in version 2.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    # Core models
    "Alert",
    "AlertConfig",
    "AlertType",
    "AlertSeverity",
]
