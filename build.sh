#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Python version: $(python --version)"
echo "Poetry version: $(poetry --version)"

# Configure poetry
poetry config virtualenvs.create false
poetry config virtualenvs.in-project false
poetry config cache-dir /opt/render/.cache/pypoetry

# Clean any existing virtualenv
rm -rf .venv || true

# Install dependencies with verbose output
echo "Installing dependencies..."
poetry install --only main --verbose --no-interaction

# Verify critical modules are installed
echo "Verifying installations..."
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
python -c "import uvicorn; print(f'Uvicorn version: {uvicorn.__version__}')"

# Set up Python path
echo "Setting up PYTHONPATH..."
export PYTHONPATH="$PYTHONPATH:${PWD}"
echo "PYTHONPATH: $PYTHONPATH"

# Verify application can be imported
echo "Verifying application import..."
python -c "from src.api.main import app; print('Application import successful')"