import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Generator

import docker
import pytest


@pytest.fixture(scope="session")
def docker_client() -> docker.DockerClient:
    """Create a Docker client for testing."""
    return docker.from_env()


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def docker_compose_file(project_root: Path) -> Path:
    """Return the path to docker-compose.yml."""
    return project_root / "docker-compose.yml"


@pytest.fixture(scope="session")
def dockerfile(project_root: Path) -> Path:
    """Return the path to Dockerfile."""
    return project_root / "Dockerfile"


@pytest.fixture(scope="function")
def test_environment() -> Generator[Dict[str, str], None, None]:
    """Provide test environment variables."""
    original_env = dict(os.environ)
    test_env = {
        "ENVIRONMENT": "test",
        "PYTHON_VERSION": "3.11",
        "SERVICE_VERSION": "test",
        "MAX_REQUEST_SIZE_MB": "2",
        "MAX_CONTENT_LENGTH": "1048576",
    }
    os.environ.update(test_env)
    yield test_env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="session")
def docker_compose_project_name() -> str:
    """Return a unique project name for docker-compose."""
    return "indexforge_test"


def run_command(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture(scope="session")
def hadolint_executable() -> str:
    """Ensure hadolint is available and return its path."""
    try:
        run_command(["hadolint", "--version"])
        return "hadolint"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("hadolint is not installed")
        return ""


@pytest.fixture(scope="session")
def trivy_executable() -> str:
    """Ensure trivy is available and return its path."""
    try:
        run_command(["trivy", "--version"])
        return "trivy"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("trivy is not installed")
        return ""
