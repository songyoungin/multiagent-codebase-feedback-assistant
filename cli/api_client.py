"""API client for agent servers."""

from typing import Any

import httpx
from rich.console import Console

console = Console()


class AgentClient:
    """Client for calling agent APIs."""

    def __init__(self, timeout: int = 120) -> None:
        """Initialize agent client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.endpoints = {
            "project_scanner": "http://localhost:8301",
            "dependency_checker": "http://localhost:8302",
            "documentation_generator": "http://localhost:8303",
            "srp_violation_detector": "http://localhost:8304",
            "naming_quality_analyzer": "http://localhost:8305",
            "orchestrator": "http://localhost:8306",
        }

    def scan_project(self, project_path: str, **kwargs: Any) -> dict[str, Any]:
        """Scan project structure.

        Args:
            project_path: Path to project to scan
            **kwargs: Additional parameters

        Returns:
            Analysis results
        """
        return self._call_agent(
            "project_scanner",
            f"Scan the project at {project_path}",
        )

    def check_dependencies(self, project_path: str, **kwargs: Any) -> dict[str, Any]:
        """Check for unused dependencies.

        Args:
            project_path: Path to project to check
            **kwargs: Additional parameters

        Returns:
            Analysis results
        """
        return self._call_agent(
            "dependency_checker",
            f"Check unused dependencies in {project_path}",
        )

    def analyze_documentation(self, project_path: str, include_private: bool = False, **kwargs: Any) -> dict[str, Any]:
        """Analyze documentation coverage.

        Args:
            project_path: Path to project to analyze
            include_private: Include private methods/functions
            **kwargs: Additional parameters

        Returns:
            Analysis results
        """
        command = f"Analyze documentation in {project_path}"
        if include_private:
            command += ", including private methods"

        return self._call_agent("documentation_generator", command)

    def check_srp_violations(
        self, project_path: str, max_items: int = 20, include_private: bool = False, **kwargs: Any
    ) -> dict[str, Any]:
        """Check for SRP violations.

        Args:
            project_path: Path to project to check
            max_items: Maximum number of items to analyze
            include_private: Include private methods/functions
            **kwargs: Additional parameters

        Returns:
            Analysis results
        """
        command = f"Analyze SRP violations in {project_path}"
        if max_items != 20:
            command += f", check up to {max_items} items"
        if include_private:
            command += ", including private methods"

        return self._call_agent("srp_violation_detector", command)

    def analyze_naming_quality(
        self, project_path: str, max_items: int = 30, include_private: bool = False, **kwargs: Any
    ) -> dict[str, Any]:
        """Analyze naming quality.

        Args:
            project_path: Path to project to analyze
            max_items: Maximum number of items to analyze
            include_private: Include private methods/functions
            **kwargs: Additional parameters

        Returns:
            Analysis results
        """
        command = f"Analyze naming quality in {project_path}"
        if max_items != 30:
            command += f", check up to {max_items} items"
        if include_private:
            command += ", including private items"

        return self._call_agent("naming_quality_analyzer", command)

    def query_orchestrator(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Send natural language query to orchestrator.

        Args:
            query: Natural language query or command
            **kwargs: Additional parameters

        Returns:
            Analysis results from orchestrator
        """
        return self._call_agent("orchestrator", query)

    def _call_agent(self, agent_name: str, command: str) -> dict[str, Any]:
        """Call agent API.

        Args:
            agent_name: Name of the agent
            command: Command to send

        Returns:
            Agent response
        """
        endpoint = self.endpoints.get(agent_name)
        if not endpoint:
            raise ValueError(f"Unknown agent: {agent_name}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{endpoint}/api/chat",
                    json={"message": command},
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result

        except httpx.ConnectError:
            console.print(f"✗ [red]Failed to connect to {agent_name}. Is the server running?[/red]")
            raise
        except httpx.TimeoutException:
            console.print(f"✗ [red]Request to {agent_name} timed out[/red]")
            raise
        except httpx.HTTPStatusError as e:
            console.print(f"✗ [red]HTTP error from {agent_name}: {e.response.status_code}[/red]")
            raise
        except Exception as e:
            console.print(f"✗ [red]Unexpected error calling {agent_name}: {e}[/red]")
            raise
