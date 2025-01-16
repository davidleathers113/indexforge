import re
from typing import Any

import pytest
import requests


def test_cors_configuration(render_config: dict[str, Any]) -> None:
    """Test CORS configuration for web services."""
    for service in render_config["services"]:
        if service["type"] == "web_service":
            env_vars = service.get("envVars", [])
            cors_vars = {env["key"]: env["value"] for env in env_vars if "CORS" in env["key"]}

            # Check if CORS is configured
            assert cors_vars, f"CORS configuration missing for service {service['name']}"

            # Check CORS origins
            if "CORS_ORIGINS" in cors_vars:
                origins = cors_vars["CORS_ORIGINS"].split(",")
                for origin in origins:
                    assert (
                        origin.startswith("https://") or origin == "*"
                    ), f"Insecure CORS origin {origin} in service {service['name']}"


def test_ssl_tls_settings(render_config: dict[str, Any]) -> None:
    """Test SSL/TLS configuration."""
    for service in render_config["services"]:
        if service["type"] == "web_service":
            env_vars = {env["key"]: env["value"] for env in service.get("envVars", [])}

            # Check SSL enforcement
            assert (
                env_vars.get("FORCE_SSL", "true").lower() == "true"
            ), f"SSL should be enforced for service {service['name']}"

            # Check HSTS configuration
            if "HSTS_ENABLED" in env_vars:
                assert (
                    env_vars["HSTS_ENABLED"].lower() == "true"
                ), f"HSTS should be enabled for service {service['name']}"


def test_secret_management(render_config: dict[str, Any]) -> None:
    """Test secret management configuration."""
    sensitive_patterns = [
        r"api[_-]key",
        r"secret[_-]key",
        r"password",
        r"token",
        r"credential",
    ]

    for service in render_config["services"]:
        for env in service.get("envVars", []):
            # Check for sensitive variables in plain text
            for pattern in sensitive_patterns:
                if re.search(pattern, env["key"], re.IGNORECASE):
                    # Value should not be set directly in render.yaml
                    assert "value" not in env or env["value"].startswith(
                        "$"
                    ), f"Sensitive variable {env['key']} should use environment substitution"

                    # Should not be synced across services
                    assert not env.get(
                        "sync", False
                    ), f"Sensitive variable {env['key']} should not be synced"


def test_authentication_configuration(render_config: dict[str, Any]) -> None:
    """Test authentication mechanism configuration."""
    for service in render_config["services"]:
        if service["type"] == "web_service":
            env_vars = {env["key"]: env["value"] for env in service.get("envVars", [])}

            # Check for authentication configuration
            auth_vars = [key for key in env_vars if "AUTH_" in key]
            assert auth_vars, f"Authentication not configured for service {service['name']}"

            # Check JWT configuration if used
            if any("JWT_" in key for key in auth_vars):
                assert (
                    "JWT_SECRET_KEY" in env_vars
                ), f"JWT secret key not configured for service {service['name']}"
                assert (
                    "JWT_ALGORITHM" in env_vars
                ), f"JWT algorithm not configured for service {service['name']}"


def test_security_headers(render_config: dict[str, Any]) -> None:
    """Test security headers configuration."""
    required_headers = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    for service in render_config["services"]:
        if service["type"] == "web_service":
            env_vars = {env["key"]: env["value"] for env in service.get("envVars", [])}

            # Check security headers configuration
            for header, value in required_headers.items():
                header_env = f"SECURITY_HEADER_{header.replace('-', '_')}"
                assert (
                    header_env in env_vars
                ), f"Security header {header} not configured for service {service['name']}"


def test_rate_limiting(render_config: dict[str, Any]) -> None:
    """Test rate limiting configuration."""
    for service in render_config["services"]:
        if service["type"] == "web_service":
            env_vars = {env["key"]: env["value"] for env in service.get("envVars", [])}

            # Check rate limiting configuration
            assert any(
                "RATE_LIMIT" in key for key in env_vars
            ), f"Rate limiting not configured for service {service['name']}"


def test_dependency_scanning() -> None:
    """Test dependencies for known vulnerabilities."""
    import subprocess

    try:
        # Run safety check on dependencies
        result = subprocess.run(
            ["poetry", "run", "safety", "check"], capture_output=True, text=True
        )

        # Check for high severity vulnerabilities
        if result.returncode != 0:
            output = result.stdout + result.stderr
            if "High severity" in output:
                pytest.fail("High severity vulnerabilities found in dependencies")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to run dependency security scan: {e!s}")


def test_render_service_security(
    render_api_base: str, render_headers: dict[str, str], render_service: dict[str, Any]
) -> None:
    """Test Render service security configuration."""
    service_id = render_service["id"]

    # Get service configuration
    response = requests.get(f"{render_api_base}/services/{service_id}", headers=render_headers)
    response.raise_for_status()
    service_config = response.json()

    # Check pull request preview settings
    assert not service_config.get(
        "autoDeploy", False
    ), "Auto-deploy should be disabled for security"

    # Check environment privacy
    assert service_config.get("envVarsPrivate", True), "Environment variables should be private"

    # Check branch protection
    assert service_config.get(
        "branchProtectionEnabled", False
    ), "Branch protection should be enabled"
