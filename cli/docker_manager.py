"""Docker Compose management for agent servers."""

import subprocess
import time
from pathlib import Path

import docker
import httpx
from rich.console import Console

console = Console()


class DockerManager:
    """Manage Docker Compose lifecycle for agent servers."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize Docker manager.

        Args:
            project_root: Root directory of the project (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.docker_compose_file = self.project_root / "docker-compose.yml"
        self.docker_client: docker.DockerClient | None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not connect to Docker daemon: {e}[/yellow]")
            console.print("[yellow]Container status checks will be limited[/yellow]")
            self.docker_client = None

    def are_containers_running(self) -> bool:
        """Check if all agent containers are running.

        Returns:
            True if all containers are running, False otherwise
        """
        if self.docker_client is None:
            return False

        try:
            containers = self.docker_client.containers.list()
            container_names = {c.name for c in containers}

            # Check for our agent containers
            required_containers = {
                "project-scanner",
                "dependency-checker",
                "documentation-generator",
                "srp-violation-detector",
                "naming-quality-analyzer",
                "orchestrator",
            }

            # Check if any required container name is in the running containers
            for required in required_containers:
                if not any(required in name for name in container_names):
                    return False

            return True
        except Exception:
            return False

    def start_containers(self) -> None:
        """Start all agent containers using docker-compose."""
        if self.are_containers_running():
            console.print("✓ [green]Servers already running[/green]")
            return

        console.print("🚀 [yellow]Starting analysis servers...[/yellow]")

        try:
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )

            if result.stdout:
                console.print(result.stdout)

            # Wait for containers to be healthy
            self._wait_for_healthy()
            console.print("✓ [green]All servers ready[/green]")

        except subprocess.CalledProcessError as e:
            console.print("✗ [red]Failed to start containers[/red]")
            if e.stderr:
                console.print(f"[red]Error: {e.stderr}[/red]")
            if e.stdout:
                console.print(f"[yellow]Output: {e.stdout}[/yellow]")
            raise
        except FileNotFoundError:
            console.print("✗ [red]docker compose command not found. Please install Docker Compose.[/red]")
            raise
        except Exception as e:
            console.print(f"✗ [red]Unexpected error: {type(e).__name__}: {e}[/red]")
            raise

    def stop_containers(self) -> None:
        """Stop all agent containers."""
        console.print("🛑 [yellow]Stopping analysis servers...[/yellow]")

        try:
            subprocess.run(
                ["docker", "compose", "down"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            console.print("✓ [green]Servers stopped[/green]")
        except subprocess.CalledProcessError as e:
            console.print("✗ [red]Failed to stop containers[/red]")
            if e.stderr:
                console.print(f"[red]Error: {e.stderr}[/red]")
            raise

    def restart_containers(self) -> None:
        """Restart all agent containers."""
        self.stop_containers()
        self.start_containers()

    def _wait_for_healthy(self, timeout: int = 60, check_interval: int = 2) -> None:
        """Wait for all agent endpoints to be healthy.

        Args:
            timeout: Maximum time to wait in seconds
            check_interval: Time between health checks in seconds
        """
        endpoints = {
            "Project Scanner": "http://localhost:8301/.well-known/agent-card.json",
            "Dependency Checker": "http://localhost:8302/.well-known/agent-card.json",
            "Documentation Generator": "http://localhost:8303/.well-known/agent-card.json",
            "SRP Violation Detector": "http://localhost:8304/.well-known/agent-card.json",
            "Naming Quality Analyzer": "http://localhost:8305/.well-known/agent-card.json",
            "Orchestrator": "http://localhost:8306/.well-known/agent-card.json",
        }

        start_time = time.time()
        healthy = set()

        while time.time() - start_time < timeout:
            for name, endpoint in endpoints.items():
                if name in healthy:
                    continue

                try:
                    response = httpx.get(endpoint, timeout=1.0)
                    if response.status_code == 200:
                        healthy.add(name)
                        console.print(f"  ✓ {name}")
                except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError):
                    pass

            if len(healthy) == len(endpoints):
                return

            time.sleep(check_interval)

        # Timeout reached
        missing = set(endpoints.keys()) - healthy
        console.print(f"⚠ [yellow]Warning: Some services not ready: {', '.join(missing)}[/yellow]")

    def get_container_status(self) -> dict[str, str]:
        """Get status of all agent containers.

        Returns:
            Dictionary mapping container names to their status
        """
        if self.docker_client is None:
            console.print("✗ [red]Docker client not initialized[/red]")
            return {}

        try:
            containers = self.docker_client.containers.list(all=True)
            status = {}

            agent_names = [
                "project-scanner",
                "dependency-checker",
                "documentation-generator",
                "srp-violation-detector",
                "naming-quality-analyzer",
                "orchestrator",
            ]

            for agent in agent_names:
                matching = [c for c in containers if agent in c.name]
                if matching:
                    status[agent] = matching[0].status
                else:
                    status[agent] = "not found"

            return status
        except Exception as e:
            console.print(f"✗ [red]Failed to get container status: {e}[/red]")
            return {}
