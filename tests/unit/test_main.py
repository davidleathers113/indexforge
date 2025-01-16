"""Entry point for main module tests.

Note: These tests have been moved to their respective modules:
- test_execution.py - Tests pipeline initialization and execution
- test_parameters.py - Tests parameter handling
- test_validation.py - Tests parameter validation
"""

from tests.unit.main.test_error_handling import (
    test_error_cleanup,
    test_error_propagation,
    test_pipeline_error_handling,
    test_validation_error_handling,
)
from tests.unit.main.test_execution import (
    test_pipeline_execution,
    test_pipeline_initialization_with_defaults,
    test_pipeline_validation,
)
from tests.unit.main.test_parameters import (
    test_argument_parsing,
    test_argument_parsing_error_handling,
    test_custom_parameters,
    test_default_parameters,
    test_parameter_coercion,
    test_parameter_defaults,
    test_parameter_types,
    test_parameter_validation,
)
from tests.unit.main.test_validation import (
    test_export_dir_required,
    test_index_url_validation,
    test_validate_numeric_ranges,
    test_validate_required_parameters,
    test_validate_url,
    test_validate_url_parameter,
    test_validate_valid_parameters,
)


__all__ = [
    # Error handling tests
    "test_error_propagation",
    "test_validation_error_handling",
    "test_pipeline_error_handling",
    "test_error_cleanup",
    # Execution flow tests
    "test_pipeline_execution",
    "test_pipeline_initialization_with_defaults",
    "test_pipeline_validation",
    # Parameter handling tests
    "test_parameter_validation",
    "test_parameter_coercion",
    "test_parameter_defaults",
    "test_parameter_types",
    "test_argument_parsing",
    "test_argument_parsing_error_handling",
    "test_custom_parameters",
    "test_default_parameters",
    # Validation tests
    "test_validate_url",
    "test_validate_required_parameters",
    "test_validate_numeric_ranges",
    "test_validate_url_parameter",
    "test_validate_valid_parameters",
    "test_export_dir_required",
    "test_index_url_validation",
]
