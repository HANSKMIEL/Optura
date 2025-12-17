import logging
import docker
import json
import tempfile
import os
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger(__name__)


class SandboxRunner:
    """Service for running tests in isolated Docker containers."""

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def run_python_tests(self, code: str, tests: str, timeout: int = None) -> Dict[str, Any]:
        """Run Python tests in a sandboxed environment."""
        if not self.client:
            return {
                "success": False,
                "error": "Docker client not available",
                "output": ""
            }

        timeout = timeout or settings.sandbox_timeout_seconds

        try:
            # Create temporary directory for code
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write code and tests
                code_file = os.path.join(tmpdir, "main.py")
                test_file = os.path.join(tmpdir, "test_main.py")

                with open(code_file, "w") as f:
                    f.write(code)

                with open(test_file, "w") as f:
                    f.write(tests)

                # Run container
                try:
                    container = self.client.containers.run(
                        "optura-sandbox-python:latest",
                        command=["python", "-m", "pytest", "/workspace/test_main.py", "-v", "--tb=short"],
                        volumes={tmpdir: {"bind": "/workspace", "mode": "ro"}},
                        mem_limit=f"{settings.sandbox_memory_limit_mb}m",
                        network_disabled=True,
                        detach=True,
                        remove=False
                    )

                    # Wait for completion
                    result = container.wait(timeout=timeout)
                    logs = container.logs().decode("utf-8")

                    # Clean up
                    container.remove()

                    return {
                        "success": result["StatusCode"] == 0,
                        "exit_code": result["StatusCode"],
                        "output": logs,
                        "error": None if result["StatusCode"] == 0 else "Tests failed"
                    }

                except docker.errors.ContainerError as e:
                    return {
                        "success": False,
                        "exit_code": e.exit_status,
                        "output": e.stderr.decode("utf-8") if e.stderr else "",
                        "error": str(e)
                    }

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    def run_node_tests(self, code: str, tests: str, timeout: int = None) -> Dict[str, Any]:
        """Run Node.js tests in a sandboxed environment."""
        if not self.client:
            return {
                "success": False,
                "error": "Docker client not available",
                "output": ""
            }

        timeout = timeout or settings.sandbox_timeout_seconds

        try:
            # Create temporary directory for code
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write code and tests
                code_file = os.path.join(tmpdir, "index.js")
                test_file = os.path.join(tmpdir, "index.test.js")
                package_file = os.path.join(tmpdir, "package.json")

                with open(code_file, "w") as f:
                    f.write(code)

                with open(test_file, "w") as f:
                    f.write(tests)

                # Create basic package.json
                package_json = {
                    "name": "sandbox-test",
                    "version": "1.0.0",
                    "scripts": {"test": "jest"},
                    "devDependencies": {"jest": "^29.0.0"}
                }
                with open(package_file, "w") as f:
                    json.dump(package_json, f)

                # Run container
                try:
                    container = self.client.containers.run(
                        "optura-sandbox-node:latest",
                        command=["npm", "test"],
                        volumes={tmpdir: {"bind": "/workspace", "mode": "ro"}},
                        mem_limit=f"{settings.sandbox_memory_limit_mb}m",
                        network_disabled=True,
                        detach=True,
                        remove=False
                    )

                    # Wait for completion
                    result = container.wait(timeout=timeout)
                    logs = container.logs().decode("utf-8")

                    # Clean up
                    container.remove()

                    return {
                        "success": result["StatusCode"] == 0,
                        "exit_code": result["StatusCode"],
                        "output": logs,
                        "error": None if result["StatusCode"] == 0 else "Tests failed"
                    }

                except docker.errors.ContainerError as e:
                    return {
                        "success": False,
                        "exit_code": e.exit_status,
                        "output": e.stderr.decode("utf-8") if e.stderr else "",
                        "error": str(e)
                    }

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    def run_tests(self, language: str, code: str, tests: str, timeout: int = None) -> Dict[str, Any]:
        """Run tests based on language."""
        if language == "python":
            return self.run_python_tests(code, tests, timeout)
        elif language in ["javascript", "typescript", "node"]:
            return self.run_node_tests(code, tests, timeout)
        else:
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
                "output": ""
            }
