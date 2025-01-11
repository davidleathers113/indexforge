from pathlib import Path

import pytest


def test_dockerfile_lint(dockerfile: Path, hadolint_executable: str) -> None:
    """Test Dockerfile using hadolint for best practices."""
    if not hadolint_executable:
        pytest.skip("hadolint not available")

    result = pytest.helpers.run_command([hadolint_executable, str(dockerfile)])
    assert result.returncode == 0, f"Dockerfile linting failed:\n{result.stderr}"


def test_security_scan(dockerfile: Path, trivy_executable: str) -> None:
    """Test Dockerfile for security vulnerabilities using trivy."""
    if not trivy_executable:
        pytest.skip("trivy not available")

    result = pytest.helpers.run_command(
        [
            trivy_executable,
            "config",
            "--severity",
            "HIGH,CRITICAL",
            "--exit-code",
            "1",
            str(dockerfile),
        ]
    )
    assert result.returncode == 0, f"Security scan failed:\n{result.stderr}"


def test_multi_stage_build(dockerfile: Path) -> None:
    """Verify that the Dockerfile uses multi-stage builds."""
    content = dockerfile.read_text()
    assert (
        "FROM" in content and content.count("FROM") > 1
    ), "Dockerfile should use multi-stage builds"
    assert "AS" in content, "Dockerfile should use named build stages"


def test_base_image_version(dockerfile: Path) -> None:
    """Verify base image has specific version tag."""
    content = dockerfile.read_text()
    assert ":latest" not in content, "Should not use 'latest' tag in base images"
    assert "${PYTHON_VERSION}" in content, "Should use versioned Python base image"


def test_security_best_practices(dockerfile: Path) -> None:
    """Test for security best practices in Dockerfile."""
    content = dockerfile.read_text()

    # Check for non-root user
    assert "useradd" in content or "adduser" in content, "Should create a non-root user"
    assert "USER" in content, "Should switch to non-root user"

    # Check for proper permissions
    assert "chown" in content, "Should set proper file ownership"

    # Check for health check
    assert "HEALTHCHECK" in content, "Should include HEALTHCHECK instruction"


def test_layer_optimization(dockerfile: Path) -> None:
    """Test for Dockerfile layer optimization."""
    content = dockerfile.read_text()

    # Check for proper ordering of layers
    assert content.find("COPY") > content.find(
        "RUN apt-get"
    ), "Should install dependencies before copying application code"

    # Check for layer combination
    assert "&& \\" in content, "Should combine RUN commands to reduce layers"

    # Check for proper cleanup
    assert "rm -rf /var/lib/apt/lists/*" in content, "Should clean up apt cache"


def test_environment_configuration(dockerfile: Path) -> None:
    """Test environment variable configuration."""
    content = dockerfile.read_text()

    # Check for environment variables
    assert "ENV" in content, "Should define environment variables"

    # Check for build arguments
    assert "ARG" in content, "Should use build arguments for flexibility"

    # Check for proper environment variable usage
    assert "${" in content, "Should use variable substitution"
