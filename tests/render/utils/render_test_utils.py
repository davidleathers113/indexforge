"""Utility functions for Render testing."""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class RenderTestUtils:
    @staticmethod
    def wait_for_deployment(
        api_base: str,
        headers: Dict[str, str],
        service_id: str,
        deployment_id: str,
        timeout: int = 300,
        check_interval: float = 5.0,
    ) -> Dict[str, Any]:
        """Wait for deployment to complete and return status."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{api_base}/services/{service_id}/deploys/{deployment_id}",
                headers=headers,
            )
            response.raise_for_status()
            deployment = response.json()

            if deployment["status"] in ["live", "failed"]:
                return deployment
            time.sleep(check_interval)

        raise TimeoutError(f"Deployment {deployment_id} did not complete within {timeout} seconds")

    @staticmethod
    def save_build_logs(
        test_data_dir: Path,
        deployment_id: str,
        logs: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save build logs and metadata to file."""
        log_file = test_data_dir / f"build_logs_{deployment_id}.json"
        data = {
            "deployment_id": deployment_id,
            "logs": logs,
            "timestamp": time.time(),
        }
        if metadata:
            data["metadata"] = metadata

        with open(log_file, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def check_build_steps(logs: List[str], required_steps: List[str]) -> Dict[str, bool]:
        """Check build steps completion status."""
        return {
            step: any(step in log and "error" not in log.lower() for log in logs)
            for step in required_steps
        }

    @staticmethod
    def get_deployment_metrics(
        api_base: str,
        headers: Dict[str, str],
        service_id: str,
        deployment_id: str,
    ) -> Dict[str, float]:
        """Get deployment metrics."""
        response = requests.get(
            f"{api_base}/services/{service_id}/deploys/{deployment_id}/metrics",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def validate_environment_config(
        service_config: Dict[str, Any],
        required_vars: List[str],
    ) -> Dict[str, bool]:
        """Validate environment configuration."""
        env_vars = {env["key"]: env["value"] for env in service_config.get("envVars", [])}
        return {var: var in env_vars for var in required_vars}

    @staticmethod
    def analyze_build_performance(
        build_duration: float,
        metrics: Dict[str, Any],
        thresholds: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze build performance against thresholds."""
        return {
            "duration_within_limit": build_duration <= thresholds["startup_time"],
            "cpu_within_limit": metrics["cpu_usage"] <= thresholds["cpu_usage"],
            "memory_within_limit": metrics["memory_usage"] <= thresholds["memory_usage"],
            "actual_duration": build_duration,
            "actual_cpu": metrics["cpu_usage"],
            "actual_memory": metrics["memory_usage"],
        }
