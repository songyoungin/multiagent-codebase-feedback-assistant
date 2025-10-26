"""A2A server for dependency checker agent."""

import uvicorn
from a2a.types import AgentSkill

from agents.dependency_checker.dependency_checker_agent import DEPENDENCY_CHECKER_AGENT
from agents.helpers.create_a2a_server import create_agent_a2a_server
from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)


def main() -> None:
    """Start the Dependency Checker Agent A2A server."""
    logger.info("Starting Dependency Checker Agent server...")

    # Define AgentSkill
    skills = [
        AgentSkill(
            id="dependency_checker",
            name="Dependency Checker",
            description="Analyze Python project dependencies and identify unused packages.",
            examples=[
                "Check unused dependencies in the current project.",
                "Analyze dependencies in /path/to/project and find unused ones.",
            ],
            tags=["dependencies", "analysis", "unused", "cleanup"],
        )
    ]

    # Create A2A server
    a2a_app = create_agent_a2a_server(
        agent=DEPENDENCY_CHECKER_AGENT,
        name="Dependency Checker Agent",
        description="Analyze Python project dependencies and identify unused packages.",
        version="0.1.0",
        skills=skills,
        url=settings.dependency_checker_agent_url,
    ).build()

    # Extract port from URL
    port = settings.get_port_from_url(settings.dependency_checker_agent_url)

    logger.info(f"Server starting on {settings.dependency_checker_agent_url}")
    logger.info(f"Binding to {settings.bind_host}:{port}")

    # Run server with Uvicorn
    uvicorn.run(
        a2a_app,
        host=settings.bind_host,
        port=port,
    )


if __name__ == "__main__":
    main()
