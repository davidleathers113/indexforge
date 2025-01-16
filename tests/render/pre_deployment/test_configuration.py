from pathlib import Path
from typing import Any

import jsonschema
import pytest


# Schema for render.yaml validation
RENDER_YAML_SCHEMA = {
    "type": "object",
    "required": ["services"],
    "properties": {
        "services": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type", "env"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["web_service", "worker", "cron", "private_service"],
                    },
                    "env": {"type": "string"},
                    "region": {"type": "string"},
                    "plan": {"type": "string"},
                    "branch": {"type": "string"},
                    "buildCommand": {"type": "string"},
                    "startCommand": {"type": "string"},
                    "envVars": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["key"],
                            "properties": {
                                "key": {"type": "string"},
                                "value": {"type": "string"},
                                "sync": {"type": "boolean"},
                            },
                        },
                    },
                    "autoDeploy": {"type": "string", "enum": ["yes", "no"]},
                    "healthCheckPath": {"type": "string"},
                    "disk": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "mountPath": {"type": "string"},
                            "sizeGB": {"type": "integer"},
                        },
                    },
                },
            },
        }
    },
}


def test_render_yaml_exists(project_root: Path) -> None:
    """Test that render.yaml exists in project root."""
    render_yaml = project_root / "render.yaml"
    assert render_yaml.exists(), "render.yaml not found in project root"
    assert render_yaml.is_file(), "render.yaml is not a file"


def test_render_yaml_valid(render_config: dict[str, Any]) -> None:
    """Test that render.yaml is valid according to schema."""
    try:
        jsonschema.validate(instance=render_config, schema=RENDER_YAML_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"render.yaml validation failed: {e!s}")


def test_required_env_vars(render_config: dict[str, Any]) -> None:
    """Test that all required environment variables are defined."""
    required_vars = {
        "PYTHON_VERSION",
        "ENVIRONMENT",
        "SERVICE_VERSION",
        "REDIS_URL",
        "DATABASE_URL",
        "WEAVIATE_URL",
    }

    for service in render_config["services"]:
        if "envVars" not in service:
            continue

        defined_vars = {env["key"] for env in service["envVars"]}
        missing_vars = required_vars - defined_vars

        assert not missing_vars, f"Missing required environment variables: {missing_vars}"


def test_health_check_paths(render_config: dict[str, Any]) -> None:
    """Test that health check paths are properly configured."""
    for service in render_config["services"]:
        if service["type"] == "web_service":
            assert (
                "healthCheckPath" in service
            ), f"Health check path not configured for web service {service['name']}"
            assert service["healthCheckPath"].startswith(
                "/"
            ), f"Health check path must start with / for service {service['name']}"


def test_resource_allocation(render_config: dict[str, Any]) -> None:
    """Test that resource allocations are reasonable."""
    for service in render_config["services"]:
        if "plan" in service:
            assert (
                service["plan"] != "free"
            ), f"Free plan not recommended for production service {service['name']}"

        if "disk" in service:
            assert (
                service["disk"]["sizeGB"] >= 1
            ), f"Disk size must be at least 1GB for service {service['name']}"


def test_security_settings(render_config: dict[str, Any]) -> None:
    """Test security-related settings."""
    for service in render_config["services"]:
        # Check for secure environment variables
        if "envVars" in service:
            secure_vars = {"DATABASE_URL", "REDIS_URL", "API_KEY", "SECRET_KEY"}
            for env in service["envVars"]:
                if env["key"] in secure_vars:
                    assert not env.get(
                        "sync", False
                    ), f"Sensitive variable {env['key']} should not be synced across services"

        # Check for auto-deploy settings
        if service["type"] == "web_service":
            assert (
                service.get("autoDeploy", "no") == "no"
            ), f"Auto-deploy should be disabled for production service {service['name']}"


def test_build_commands(render_config: dict[str, Any]) -> None:
    """Test that build commands are properly configured."""
    for service in render_config["services"]:
        if service["env"] == "python":
            build_cmd = service.get("buildCommand", "")
            assert (
                "poetry install" in build_cmd
            ), f"Poetry install not found in build command for service {service['name']}"

            start_cmd = service.get("startCommand", "")
            assert start_cmd, f"Start command not configured for service {service['name']}"


def test_dependencies_configuration(render_config: dict[str, Any]) -> None:
    """Test that service dependencies are properly configured."""
    service_names = {service["name"] for service in render_config["services"]}

    for service in render_config["services"]:
        if "envVars" in service:
            for env in service["envVars"]:
                # Check if environment variable references another service
                for service_name in service_names:
                    if service_name in env.get("value", ""):
                        assert service.get(
                            "dependsOn", []
                        ), f"Service {service['name']} should declare dependency on {service_name}"
