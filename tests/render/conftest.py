import json
import os
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
import requests
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def render_api_token() -> str:
    """Get Render API token from environment."""
    token = os.getenv("RENDER_API_TOKEN")
    if not token:
        pytest.skip("RENDER_API_TOKEN not set")
    return token


@pytest.fixture(scope="session")
def render_api_base() -> str:
    """Get Render API base URL."""
    return "https://api.render.com/v1"


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def render_config(project_root: Path) -> Dict[str, Any]:
    """Load render.yaml configuration."""
    config_path = project_root / "render.yaml"
    if not config_path.exists():
        pytest.skip("render.yaml not found")
    with open(config_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def render_headers(render_api_token: str) -> Dict[str, str]:
    """Create headers for Render API requests."""
    return {
        "Authorization": f"Bearer {render_api_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="function")
def render_service(
    render_api_base: str, render_headers: Dict[str, str]
) -> Generator[Dict[str, Any], None, None]:
    """Create a test service on Render."""
    # Create service
    service_config = {
        "name": "indexforge-test",
        "type": "web_service",
        "env": "python",
        "region": "oregon",
        "branch": "main",
        "autoDeploy": "no",
    }

    response = requests.post(
        f"{render_api_base}/services", headers=render_headers, json=service_config
    )
    response.raise_for_status()
    service = response.json()

    yield service

    # Cleanup
    requests.delete(f"{render_api_base}/services/{service['id']}", headers=render_headers)


@pytest.fixture(scope="function")
def deployment_id(
    render_api_base: str, render_headers: Dict[str, str], render_service: Dict[str, Any]
) -> str:
    """Create a test deployment and return its ID."""
    response = requests.post(
        f"{render_api_base}/services/{render_service['id']}/deploys", headers=render_headers
    )
    response.raise_for_status()
    return response.json()["id"]


def wait_for_deployment(
    render_api_base: str,
    render_headers: Dict[str, str],
    service_id: str,
    deployment_id: str,
    timeout: int = 600,
    interval: int = 10,
) -> Dict[str, Any]:
    """Wait for deployment to complete and return status."""
    import time

    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(
            f"{render_api_base}/services/{service_id}/deploys/{deployment_id}",
            headers=render_headers,
        )
        response.raise_for_status()
        status = response.json()["status"]

        if status in {"live", "failed", "cancelled"}:
            return response.json()

        time.sleep(interval)

    raise TimeoutError(f"Deployment did not complete within {timeout} seconds")


@pytest.fixture(scope="session")
def performance_thresholds() -> Dict[str, Any]:
    """Define performance test thresholds."""
    return {
        "startup_time": 30,  # seconds
        "response_time_p95": 500,  # milliseconds
        "error_rate": 0.001,  # 0.1%
        "memory_usage": 0.8,  # 80%
        "cpu_usage": 0.7,  # 70%
        "recovery_time": 300,  # seconds
    }


@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """Return path to test data directory."""
    data_dir = project_root / "tests" / "render" / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def save_test_results(results: Dict[str, Any], test_data_dir: Path, test_name: str) -> None:
    """Save test results to JSON file."""
    results_file = test_data_dir / f"{test_name}_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)


def load_test_results(test_data_dir: Path, test_name: str) -> Dict[str, Any]:
    """Load test results from JSON file."""
    results_file = test_data_dir / f"{test_name}_results.json"
    if not results_file.exists():
        return {}
    with open(results_file) as f:
        return json.load(f)
