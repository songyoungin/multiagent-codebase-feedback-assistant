"""Factory functions for creating A2A servers."""

import asyncio
import time
from collections.abc import Sequence
from typing import Any, cast

import httpx
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from fastapi import APIRouter, Query
from google.adk import Agent
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from common.logger import get_logger

logger = get_logger(__name__)

START_TIME = time.time()


class SubAgent:
    """Sub-agent identification info."""

    def __init__(self, name: str, public_host: str, public_port: int) -> None:
        """Initialize SubAgent instance.

        Args:
            name: Sub-agent name
            public_host: Public host
            public_port: Public port
        """
        self.name = name
        self.public_host = public_host
        self.public_port = public_port
        self.base_url = f"http://{public_host}:{public_port}"


async def _ping_one(
    client: httpx.AsyncClient, dependency: SubAgent, include_dependencies: bool
) -> dict[str, Any]:
    """Check agent health via A2A health.ping, fallback to /health endpoint.

    Args:
        client: httpx AsyncClient instance
        dependency: Sub-agent to check
        include_dependencies: Include dependency status

    Returns:
        Agent status dictionary
    """
    # Try A2A JSON-RPC health.ping first
    try:
        t0 = time.time()
        r = await client.post(
            f"{dependency.base_url}/a2a",
            json={
                "jsonrpc": "2.0",
                "id": "ping",
                "method": "health.ping",
                "params": {"include_dependencies": include_dependencies},
            },
        )
        latency_ms = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            body = r.json()
            result = body.get("result") or {}
            status = result.get("status", "ok")
            version = result.get("version")
            return {
                "status": status,
                "latency_ms": latency_ms,
                "version": version,
                "url": dependency.base_url,
            }
    except Exception:
        pass

    # Fallback to HTTP /health endpoint
    try:
        t0 = time.time()
        params = {"include_dependencies": "1"} if include_dependencies else {}
        r = await client.get(f"{dependency.base_url}/health", params=params)
        latency_ms = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            body = r.json()
            status = body.get("status", "ok")
            version = body.get("version")
            return {
                "status": status,
                "latency_ms": latency_ms,
                "version": version,
                "url": dependency.base_url,
            }
    except Exception:
        pass

    return {"status": "down", "latency_ms": None, "url": dependency.base_url}


async def _fetch_dependencies_snapshot(
    deps: Sequence[SubAgent],
    *,
    include_dependencies: bool,
    timeout_sec: float = 1.0,
) -> dict[str, Any]:
    """Ping sub-agents concurrently and create status snapshot.

    Args:
        deps: List of sub-agents
        include_dependencies: Include dependency status
        timeout_sec: Timeout in seconds

    Returns:
        Status snapshot by sub-agent name
    """
    if not deps:
        return {}
    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        results = await asyncio.gather(
            *[_ping_one(client, d, include_dependencies) for d in deps],
            return_exceptions=False,
        )
    return {dep.name: res for dep, res in zip(deps, results, strict=False)}


def _build_health_payload(
    app_name: str,
    version: str,
    *,
    include_dependencies: bool = False,
    deps_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build health check response payload.

    Args:
        app_name: Application name
        version: Application version
        include_dependencies: Include dependency status
        deps_snapshot: Dependency status snapshot

    Returns:
        Health check payload
    """
    uptime_sec = int(time.time() - START_TIME)
    payload: dict[str, Any] = {
        "status": "ok",
        "service": app_name,
        "version": version,
        "uptime_sec": uptime_sec,
        "dependencies": {},
    }
    if include_dependencies and deps_snapshot:
        payload["dependencies"] = deps_snapshot
        if any((v.get("status") != "ok") for v in deps_snapshot.values()):
            payload["status"] = "degraded"

    return payload


class HealthAwareRequestHandler(DefaultRequestHandler):
    """Request handler with immediate health.ping response and optional sub-agent aggregation."""

    def __init__(
        self,
        *,
        agent_executor: A2aAgentExecutor,
        task_store: InMemoryTaskStore,
        app_name: str,
        version: str,
        sub_agents: Sequence[SubAgent] | None = None,
        deps_timeout_sec: float = 1.0,
    ) -> None:
        """Initialize HealthAwareRequestHandler.

        Args:
            agent_executor: A2A agent executor
            task_store: Task store
            app_name: Application name
            version: Application version
            sub_agents: List of sub-agents
            deps_timeout_sec: Dependency check timeout
        """
        super().__init__(agent_executor=agent_executor, task_store=task_store)
        self._app_name = app_name
        self._version = version
        self._sub_agents = tuple(sub_agents) if sub_agents else tuple()
        self._deps_timeout_sec = deps_timeout_sec

    async def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle health.ping requests.

        Args:
            request: A2A JSON-RPC request

        Returns:
            A2A JSON-RPC response
        """
        if request.get("method") == "health.ping":
            params = request.get("params") or {}
            include_dependencies = bool(params.get("include_dependencies", False))

            deps_snapshot = None
            if include_dependencies and self._sub_agents:
                deps_snapshot = await _fetch_dependencies_snapshot(
                    self._sub_agents,
                    include_dependencies=True,
                    timeout_sec=self._deps_timeout_sec,
                )

            result = _build_health_payload(
                self._app_name,
                self._version,
                include_dependencies=include_dependencies,
                deps_snapshot=deps_snapshot,
            )
            return {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
        return cast(dict[str, Any], await super().handle(request))


def create_agent_a2a_server(
    agent: Agent,
    name: str,
    description: str,
    version: str,
    skills: Sequence[AgentSkill],
    url: str,
    sub_agents: Sequence[SubAgent] | None = None,
    deps_timeout_sec: float = 1.0,
) -> A2AFastAPIApplication:
    """Create A2A server for an ADK agent.

    Args:
        agent: ADK agent instance
        name: Agent display name
        description: Agent description
        version: Agent version
        skills: List of AgentSkill objects
        url: Public URL for agent card (e.g., http://localhost:8301)
        sub_agents: List of sub-agents
        deps_timeout_sec: Sub-agent dependency check timeout

    Returns:
        A2AFastAPIApplication instance
    """
    capabilities = AgentCapabilities(streaming=True)

    # Ensure URL ends with /
    agent_card_url = url if url.endswith("/") else f"{url}/"
    logger.info(f"Agent card for {name} is created at URL: {agent_card_url}")

    agent_card = AgentCard(
        name=name,
        description=description,
        url=agent_card_url,
        version=version,
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=skills,
    )

    runner = Runner(
        app_name=agent_card.name,
        agent=agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    executor = A2aAgentExecutor(runner=runner)

    request_handler = HealthAwareRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        app_name=agent_card.name,
        version=agent_card.version,
        sub_agents=sub_agents,
        deps_timeout_sec=deps_timeout_sec,
    )

    return A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)


def attach_http_health(
    app: A2AFastAPIApplication,
    *,
    app_name: str,
    version: str,
    sub_agents: Sequence[SubAgent] | None = None,
    deps_timeout_sec: float = 1.0,
) -> None:
    """Attach HTTP /health endpoint to the app.

    Args:
        app: A2AFastAPIApplication instance
        app_name: Application name
        version: Application version
        sub_agents: List of sub-agents
        deps_timeout_sec: Dependency check timeout
    """
    router = APIRouter()

    @router.get("/health")
    async def health(
        include_dependencies: bool = Query(
            default=False, description="Include sub-agent status in response"
        ),
    ) -> dict[str, Any]:
        """Health check endpoint.

        Args:
            include_dependencies: Include sub-agent status

        Returns:
            Health check result
        """
        deps_snapshot = None
        if include_dependencies and sub_agents:
            deps_snapshot = await _fetch_dependencies_snapshot(
                sub_agents,
                include_dependencies=True,
                timeout_sec=deps_timeout_sec,
            )
        return _build_health_payload(
            app_name,
            version,
            include_dependencies=include_dependencies,
            deps_snapshot=deps_snapshot,
        )

    app.include_router(router)
