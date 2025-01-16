#!/bin/bash

# Setup script for development environment

# Ensure we're in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Set up environment variables
echo "Setting up environment variables..."
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

echo "Development environment setup complete!"