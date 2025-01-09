"""Package setup configuration for IndexForge.

This module configures the package installation settings, including dependencies,
version requirements, and package structure. It uses setuptools to manage the
package configuration and installation process.

The package requires Python 3.11 or later and includes dependencies for:
- Machine learning and data processing (transformers, torch, scikit-learn)
- Data manipulation (numpy, pandas)
- Caching (redis)
- Universal file indexing and processing

To install the package:
```bash
# Install in development mode
pip install -e .

# Install from the current directory
pip install .
```

Note:
    The package is structured with all source code in the 'src' directory,
    following the src-layout pattern for Python packages.
"""

from setuptools import find_packages, setup

setup(
    name="indexforge",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "transformers",
        "redis",
        "torch",
        "numpy",
        "pandas",
        "scikit-learn",
    ],
    python_requires=">=3.11",
    description="Universal file indexing and processing system",
)
