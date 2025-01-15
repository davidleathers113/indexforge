# Contributing to IndexForge

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/indexforge.git
   cd indexforge
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the package in development mode:

   ```bash
   pip install -e .
   ```

4. Install development dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

5. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Code Quality Standards

1. **Testing**

   - Write unit tests for new functionality
   - Maintain test coverage above 80%
   - Run tests with `pytest`

2. **Code Style**

   - Use Black for Python code formatting
   - Use isort for import sorting
   - Follow PEP 8 guidelines
   - Run pre-commit hooks before committing

3. **Documentation**
   - Add docstrings to all public functions and classes
   - Keep API documentation up to date
   - Include examples in docstrings when helpful

## Pull Request Process

1. Update the README.md with details of changes to the interface, if applicable.
2. Update the requirements.txt if you've added new dependencies.
3. The PR will be merged once you have the sign-off of at least one other developer.

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issue tracker](../../issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](../../issues/new).

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
