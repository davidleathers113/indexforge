# Alert System Migration Guide

## Deprecation Notice

The module `src.core.monitoring.alerts.models` is deprecated and will be removed in version 2.0.0.
Users should migrate to the new import paths as described below.

## Migration Steps

### 1. Update Import Statements

Replace deprecated imports with their new counterparts:

```python
# Old style (deprecated)
from src.core.monitoring.alerts.models import Alert, AlertConfig, AlertType, AlertSeverity

# New style
from src.core.monitoring.alerts.models.alert import Alert
from src.core.monitoring.alerts.models.config import AlertConfig
from src.core.monitoring.alerts.models.types import AlertType, AlertSeverity
```

### 2. Update Type Hints

If you're using type hints, update them to use the new import paths:

```python
# Old style (deprecated)
from src.core.monitoring.alerts.models import Alert

def process_alert(alert: Alert) -> None:
    ...

# New style
from src.core.monitoring.alerts.models.alert import Alert

def process_alert(alert: Alert) -> None:
    ...
```

### 3. Check for Deprecation Warnings

Run your tests with deprecation warnings enabled to find any remaining uses of the deprecated imports:

```bash
python -Wd tests/
```

## Timeline

- Version 1.0.0: Deprecation warnings introduced
- Version 2.0.0: Old import paths removed

## Benefits of Migration

1. **Better Code Organization**: Each model in its own module
2. **Clearer Dependencies**: Explicit imports show what's being used
3. **Improved Maintainability**: Easier to update and test individual components
4. **Type Safety**: Better static type checking support

## Need Help?

If you encounter any issues during migration, please:

1. Check the documentation at `docs/alerts/`
2. Run tests with deprecation warnings enabled
3. File an issue if you find any problems
