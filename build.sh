#!/usr/bin/env bash
# exit on error
set -o errexit

# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
$HOME/.local/bin/poetry config virtualenvs.create false
$HOME/.local/bin/poetry install --no-dev