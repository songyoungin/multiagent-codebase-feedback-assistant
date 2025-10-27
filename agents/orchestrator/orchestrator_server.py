"""A2A server for Orchestrator agent."""

import uvicorn
from a2a.types import AgentSkill

from agents.helpers.create_a2a_server import create_agent_a2a_server
from agents.orchestrator.orchestrator_agent import ORCHESTRATOR_AGENT
from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)


def main() -> None:
    """Start the Orchestrator Agent A2A server."""
    logger.info("Starting Orchestrator Agent server...")

    # Define AgentSkill
    skills = [
        AgentSkill(
            id="orchestrator",
            name="Orchestrator",
            description="Coordinate multiple agents to provide comprehensive codebase analysis.",
            examples=[
                "Analyze the entire project at /path/to/project.",
                "Run all analyses on my codebase.",
                "Give me a comprehensive code quality report.",
            ],
            tags=["orchestration", "comprehensive", "multi-agent", "coordinator"],
        )
    ]

    # Create A2A server
    a2a_app = create_agent_a2a_server(
        agent=ORCHESTRATOR_AGENT,
        name="Orchestrator Agent",
        description="Coordinate multiple agents to provide comprehensive codebase analysis.",
        version="0.1.0",
        skills=skills,
        url=settings.orchestrator_agent_url,
    ).build()

    # Extract port from URL
    port = settings.get_port_from_url(settings.orchestrator_agent_url)

    logger.info(f"Server starting on {settings.orchestrator_agent_url}")
    logger.info(f"Binding to {settings.bind_host}:{port}")

    # Run server with Uvicorn
    uvicorn.run(
        a2a_app,
        host=settings.bind_host,
        port=port,
    )


if __name__ == "__main__":
    main()
