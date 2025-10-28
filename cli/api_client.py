"""API client for agent servers."""

from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientCallContext, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart
from rich.console import Console

console = Console()


class AgentClient:
    """Client for calling agent APIs using A2A protocol."""

    def __init__(self, timeout: int = 600) -> None:
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
        """Call agent API using A2A protocol.

        Args:
            agent_name: Name of the agent
            command: Command to send

        Returns:
            Agent response as dict with 'response' key
        """
        import asyncio

        endpoint = self.endpoints.get(agent_name)
        if not endpoint:
            raise ValueError(f"Unknown agent: {agent_name}")

        try:
            result = asyncio.run(self._async_call_agent(endpoint, command))
            return result
        except httpx.ConnectError:
            console.print(f"✗ [red]Failed to connect to {agent_name}. Is the server running?[/red]")
            raise
        except httpx.TimeoutException:
            console.print(f"✗ [red]Request to {agent_name} timed out[/red]")
            raise
        except Exception as e:
            console.print(f"✗ [red]Unexpected error calling {agent_name}: {e}[/red]")
            raise

    async def _async_call_agent(self, agent_url: str, command: str) -> dict[str, Any]:
        """Async implementation of agent call using A2A protocol.

        Args:
            agent_url: Agent URL to connect to
            command: Command to send

        Returns:
            Dict with 'response' key containing agent's final message
        """
        async with httpx.AsyncClient(timeout=self.timeout) as httpx_client:
            # Get Agent Card
            card_resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
            card = await card_resolver.get_agent_card()

            # Override card URL to use localhost instead of internal Docker hostname
            # This is necessary because CLI runs outside Docker but agents run inside
            card.url = agent_url

            # Create client with streaming enabled
            client_config = ClientConfig(httpx_client=httpx_client, streaming=True)
            factory = ClientFactory(config=client_config)
            client = factory.create(card=card)

            # Send message
            request = Message(
                message_id=str(uuid4()),
                role=Role.user,
                parts=[Part(TextPart(text=command))],
            )

            context = ClientCallContext()
            result = client.send_message(request, context=context)

            # Collect streaming events
            last_event = None
            async for event in result:
                last_event = event

            # Extract final message from task history
            if last_event is not None:
                task = self._extract_task_from_event(last_event)
                final_message = self._get_final_message_text(task)
                return {"response": final_message}

            return {"response": "No response from agent"}

    def _extract_task_from_event(self, event: Any) -> Any:
        """Extract Task object from event.

        Args:
            event: Event from streaming response (can be tuple or Task)

        Returns:
            Task object
        """
        return event[0] if isinstance(event, (tuple, list)) else event

    def _get_final_message_text(self, task: Any) -> str:
        """Get final message text from Task history.

        Args:
            task: Task object containing history

        Returns:
            Final message text or empty string
        """
        if not hasattr(task, "history"):
            return ""

        history = list(getattr(task, "history", []))
        if not history:
            return ""

        last_message = history[-1]
        if not hasattr(last_message, "parts"):
            return ""

        for part in last_message.parts:
            part_data = part.root if hasattr(part, "root") else part
            if hasattr(part_data, "text"):
                text = part_data.text
                return str(text) if text is not None else ""

        return ""
