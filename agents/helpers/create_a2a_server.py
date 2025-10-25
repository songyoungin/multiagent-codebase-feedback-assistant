"""Factory functions for creating A2A servers."""

from collections.abc import Sequence

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.agents.base_agent import BaseAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from common.logger import get_logger

logger = get_logger(__name__)


def create_agent_a2a_server(
    agent: BaseAgent,
    name: str,
    description: str,
    version: str,
    skills: Sequence[AgentSkill],
    url: str,
) -> A2AFastAPIApplication:
    """Create A2A server for an ADK agent.

    Args:
        agent: ADK agent instance
        name: Agent display name
        description: Agent description
        version: Agent version
        skills: List of AgentSkill objects
        url: Public URL for agent card (e.g., http://localhost:8301)

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
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text", "text/plain"],
        capabilities=capabilities,
        skills=list(skills),
    )

    runner = Runner(
        app_name=agent_card.name,
        agent=agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    executor = A2aAgentExecutor(runner=runner)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    return A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)
