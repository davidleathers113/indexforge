# Performance Comparator

A tool for comparing performance metrics between Weaviate versions 3.x and 4.x.

## Features

- Load and analyze test results from different Weaviate versions
- Compare key performance metrics including import and search operations
- Generate detailed markdown reports with findings and recommendations
- Support for both specific result files and automatic latest result detection

## Installation

```bash
# Install dependencies
poetry install
```

## Usage

```bash
# Basic usage with default directories
python -m performance_comparator.main

# Specify custom directories
python -m performance_comparator.main \
    --results-dir path/to/results \
    --output-dir path/to/reports

# Use specific result files
python -m performance_comparator.main \
    --v3-results path/to/v3_results.json \
    --v4-results path/to/v4_results.json

# Enable file logging
python -m performance_comparator.main \
    --log-file path/to/comparison.log
```

## Directory Structure

```
performance_comparator/
├── __init__.py           # Package initialization
├── main.py              # Main entry point
├── data_loader.py       # Functions for loading test results
├── metrics_comparator.py # Metric comparison logic
├── report_generator.py  # Report generation utilities
├── pyproject.toml      # Project dependencies and configuration
└── README.md           # This file
```

## Metrics Compared

### Import Metrics

- Import Duration (seconds)
- Documents per Second
- Failed Imports

### Search Metrics

- Search Duration (seconds)
- Queries per Second
- Average Query Time (seconds)
- Failed Queries

## Report Format

The generated report includes:

1. Test Parameters
   - Document Count
   - Query Count
   - Test Duration
2. Metric Comparison Tables
3. Key Findings
   - Significant improvements/degradations
4. Recommendations
   - Areas requiring investigation
   - Failed operations to address

## Development

```bash
# Install development dependencies
poetry install --with dev

# Format code
poetry run black .

# Run linting
poetry run ruff check .

# Run type checking
poetry run mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
