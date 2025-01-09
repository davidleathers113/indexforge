# Template Test Requirements

## Test Cases

### 1. Basic Formatting Tests

#### test_macro_indentation.py

- **Purpose**: Test that macro calls maintain proper indentation
- **Requirements**:
  - Import macros with context from template files
  - Proper indentation of mock setup code
  - Proper indentation of verification code
  - Support for side effects in mock setup
  - Support for ordered/unordered mock call verification
  - Generated code must be valid Python

#### test_decorator_basic_formatting.py

- **Purpose**: Test basic formatting of decorator test templates
- **Requirements**:
  - Multi-line docstring formatting with:
    - Title
    - Purpose
    - Numbered steps
  - Section comments (setup, execute, verify)
  - Proper indentation of each section
  - Support for logging setup
  - Support for mock creation and verification
  - Preservation of empty lines between sections

### 2. Complex Indentation Tests

#### test_nested_block_formatting.py

- **Purpose**: Test indentation of nested code blocks
- **Requirements**:
  - Support for multiple levels of conditional nesting
  - Proper indentation at each nesting level
  - Consistent comment indentation within blocks
  - Variable assignment indentation
  - Whitespace control with {%- -%} tags
  - Preservation of block structure
  - Support for conditional rendering

#### test_nested_conditional_indentation.py

- **Purpose**: Test indentation of nested if statements
- **Requirements**:
  - Support for multiple levels of conditional nesting
  - Proper handling of mixed condition states (true/false)
  - Empty function handling with pass statement
  - Valid Python code generation in all condition states
  - Import macros with context
  - Variable assignment at different nesting levels
  - Logging support for debugging
  - Code validation through compilation
  - Test cases for:
    - All conditions true
    - Mixed conditions
    - All conditions false

#### test_mixed_loop_conditional_indentation.py

- **Purpose**: Test indentation of mixed loops and conditionals
- **Requirements**:
  - Support for nested loops within conditionals
  - Support for conditionals within loops
  - Loop variable access (loop.index)
  - Comment indentation within loops
  - Variable assignment within nested structures
  - Function calls within conditional blocks
  - Whitespace control with {%- -%} tags
  - Complex data structure iteration
  - Test cases for:
    - Nested loops with conditions
    - Variable assignments in loops
    - Conditional function calls

#### test_multiline_function_args_indentation.py

- **Purpose**: Test indentation of function arguments
- **Requirements**:
  - Support for multiline function calls
  - Proper argument indentation
  - Handling of positional and keyword arguments
  - Loop-based argument generation
  - Comma handling for argument lists
  - Last item comma control
  - Empty line preservation between calls
  - Test cases for:
    - Complex function calls
    - Mock assertions
    - Mixed argument types

#### test_multiline_assertion_indentation.py

- **Purpose**: Test indentation of assertion statements
- **Requirements**:
  - Support for complex assertions:
    - any() expressions
    - all() expressions
    - Multiple conditions
    - Generator expressions
  - Proper indentation of:
    - Multi-line assertions
    - Assertion messages
    - Compound conditions
  - Assertion ordering preservation
  - Empty assertion list handling
  - Import assertion macros with context
  - Code validation through compilation
  - Test cases for:
    - Complex assertions
    - Empty assertions
    - Basic structure preservation

### 3. Special Cases

#### test_context_manager_indentation.py

- **Purpose**: Test indentation of context manager blocks
- **Requirements**:
  - Support for context manager setup:
    - Mock creation
    - **enter** and **exit** method setup
    - Return value configuration
  - Proper indentation of:
    - with statements
    - Nested function definitions
    - Decorator application
    - Function body
  - Conditional context manager usage
  - Empty function handling
  - Import setup macros with context
  - Code validation through compilation
  - Test cases for:
    - With context manager
    - Without context manager
    - Nested decorators

#### test_try_except_indentation.py

- **Purpose**: Test indentation of exception handling blocks
- **Requirements**:
  - Support for complete try-except-finally structure
  - Proper indentation of:
    - try block
    - except block with exception binding
    - finally block
  - Loop-based content generation in each block
  - Multiple operations per block
  - Whitespace control with {%- -%} tags
  - Test cases for:
    - Multiple operations
    - Error handling
    - Cleanup steps

#### test_verification_block_formatting.py

- **Purpose**: Test formatting of verification blocks
- **Requirements**:
  - Support for multi-line assertions:
    - Complex conditions with line breaks
    - Generator expressions
    - Assertion messages
  - Proper indentation of:
    - Assertion blocks
    - Compound conditions
    - Generator expressions
    - Error messages
  - Preservation of:
    - Line breaks
    - Indentation levels
    - Block comments
  - Test cases for:
    - Complex assertions
    - Multiple assertions
    - Nested conditions

### 4. Template Features

#### test_decorator_templates.py

- **Purpose**: Test full decorator test generation
- **Requirements**:
  - Support for different decorator types:
    - Cache decorator
    - Retry decorator
  - Template structure:
    - Mock setup section
    - Function generation section
    - Verification section
  - Decorator configuration:
    - Dynamic arguments
    - Named parameters
    - Default values
  - Function generation:
    - Dynamic arguments
    - Function body
    - Return values
  - Mock setup:
    - Cache mocks
    - Serialization mocks
    - Retry mocks
    - Side effects
  - Verification:
    - Result checking
    - Mock call verification
    - Cache operations
    - Serialization calls
    - Log messages
  - Indentation support:
    - Nested blocks
    - Conditional sections
    - Multi-line statements
  - Template features:
    - Conditional rendering
    - Loop handling
    - Filter usage (indent)
    - Whitespace control

#### test_mock_verification_formatting.py

- **Purpose**: Test mock verification formatting
- **Requirements**: TBD

#### test_template_rendering.py

- **Purpose**: Test general template rendering
- **Requirements**:
  - Basic indentation:
    - Function definitions
    - Variable assignments
    - Indented blocks
  - Conditional indentation:
    - If-else blocks
    - Block content
  - Macro indentation:
    - Macro definitions
    - Macro calls
    - Nested macros
    - Indent filter usage
  - Decorator indentation:
    - Single-line decorators
    - Function definitions
  - Verification blocks:
    - Multiple assertions
    - Dynamic conditions
    - Error messages
  - Mixed content:
    - Comments
    - Setup code
    - Function calls
    - Assertions
  - Test cases for:
    - Basic indentation
    - Conditional blocks
    - Macro usage
    - Decorator formatting
    - Verification blocks
    - Mixed content

## Required Macros

### Mock Setup Macros (mocks.py.jinja)

```jinja
{% macro setup(mock_name, return_value=None, side_effect=None) %}
{% macro setup_cache_mock(config=None) %}
{% macro setup_serialization(config=None) %}
{% macro setup_retry_mocks(config=None) %}
```

### Verification Macros (assertions.py.jinja)

```jinja
{% macro verify_mock_calls(mock_name, calls, ordered=True) %}
{% macro verify_result(actual, expected, msg=None) %}
{% macro verify_retry_behavior(mock_name, config) %}
{% macro verify_cache_call(mock_name, config) %}
{% macro verify_serialization_calls(mock_name, calls) %}
{% macro verify_single_log(mock_name, level, message) %}
```

## Required Features

### 1. Indentation Support

- Proper handling of nested blocks
- Preservation of empty lines
- Consistent indentation levels
- Support for the `indent` filter
- Special handling for:
  - Function definitions
  - Docstrings
  - Comments
  - Multi-line statements
  - Nested blocks
  - Conditional blocks
  - Variable assignments
  - Empty functions with pass
  - Loops with conditions
  - Function calls
  - Function arguments
  - Argument lists
  - Mock assertions
  - Complex assertions
  - Generator expressions
  - Context manager blocks
  - Nested functions
  - Decorators
  - Try-except blocks
  - Exception handling
  - Finally blocks
  - Verification blocks
  - Multi-line assertions
  - Decorator arguments
  - Mock setup blocks

### 2. Template Context

- Mock configuration objects
- Verification helpers
- Test setup utilities
- Logging configuration
- Support for:
  - Default values
  - Optional parameters
  - Complex data structures
  - Nested conditions
  - Boolean flags
  - Mixed condition states
  - Debug logging
  - Loop variables
  - Nested iterations
  - Argument formatting
  - Last item handling
  - Assertion messages
  - Compound conditions
  - Context manager setup
  - Method mocking
  - Exception binding
  - Error handling
  - Cleanup operations
  - Verification blocks
  - Multi-line assertions
  - Decorator configuration
  - Mock side effects
  - Dynamic arguments

### 3. Code Generation

- Valid Python syntax
- Proper docstring formatting
- Decorator handling
- Exception handling
- Context manager support
- Support for:
  - Comments
  - Empty lines
  - Multi-line statements
  - Nested blocks
  - Variable assignments
  - Empty functions
  - Code compilation validation
  - Loop constructs
  - Function calls
  - Argument lists
  - Mock assertions
  - Complex assertions
  - Generator expressions
  - Context managers
  - Nested functions
  - Decorators
  - Try-except-finally blocks
  - Exception binding
  - Error handling
  - Verification blocks
  - Multi-line assertions
  - Decorator arguments
  - Mock setup
  - Test sections

### 4. Special Features

- Conditional rendering
- Loop handling
- Macro imports with context
- Template inheritance
- Support for:
  - Whitespace control
  - Line continuation
  - Block delimiters
  - Nested conditions
  - Comment preservation
  - Debug output
  - Code validation
  - Loop variables
  - Complex data structures
  - Argument formatting
  - Last item handling
  - Assertion ordering
  - Empty list handling
  - Context manager setup
  - Method mocking
  - Exception handling
  - Error recovery
  - Verification blocks
  - Line break preservation
  - Decorator types
  - Mock configuration
