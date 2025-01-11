"""Utility functions for Docker testing."""

import time
from typing import Dict, List, Optional

import docker
import psutil


class DockerTestUtils:
    @staticmethod
    def check_logs(logs: List[str], patterns: List[str]) -> bool:
        """Check if all patterns exist in logs."""
        return all(any(pattern in log for log in logs) for pattern in patterns)

    @staticmethod
    def wait_for_container_health(
        container: docker.models.containers.Container,
        timeout: int = 30,
        check_interval: float = 0.5,
    ) -> bool:
        """Wait for container to become healthy."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            health = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if health == "healthy":
                return True
            time.sleep(check_interval)
        return False

    @staticmethod
    def get_container_resource_usage(
        container: docker.models.containers.Container,
    ) -> Dict[str, float]:
        """Get container CPU and memory usage."""
        stats = container.stats(stream=False)
        cpu_stats = stats["cpu_stats"]
        precpu_stats = stats["precpu_stats"]
        memory_stats = stats["memory_stats"]

        cpu_usage = (
            (cpu_stats["cpu_usage"]["total_usage"] - precpu_stats["cpu_usage"]["total_usage"])
            / (cpu_stats["system_cpu_usage"] - precpu_stats["system_cpu_usage"])
            * 100.0
            * psutil.cpu_count()
        )

        memory_usage = (
            memory_stats["usage"] / memory_stats["limit"]
            if "usage" in memory_stats and "limit" in memory_stats
            else 0.0
        ) * 100.0

        return {"cpu_usage": cpu_usage, "memory_usage": memory_usage}

    @staticmethod
    def verify_file_permissions(
        container: docker.models.containers.Container,
        path: str,
        expected_mode: str,
        expected_user: Optional[str] = None,
    ) -> bool:
        """Verify file permissions inside container."""
        result = container.exec_run(f"stat -c '%a %U' {path}")
        if result.exit_code != 0:
            return False

        actual_mode, actual_user = result.output.decode().strip().split()
        return actual_mode == expected_mode and (
            expected_user is None or actual_user == expected_user
        )

    @staticmethod
    def check_process_isolation(
        container: docker.models.containers.Container,
        expected_processes: List[str],
    ) -> bool:
        """Check process isolation in container."""
        result = container.exec_run("ps aux")
        if result.exit_code != 0:
            return False

        processes = result.output.decode().split("\n")
        return all(any(proc in process for process in processes) for proc in expected_processes)
