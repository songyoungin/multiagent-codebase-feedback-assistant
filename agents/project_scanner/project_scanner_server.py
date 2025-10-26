"""A2A server for project scanner agent."""

import uvicorn
from a2a.types import AgentSkill

from agents.helpers.create_a2a_server import create_agent_a2a_server
from agents.project_scanner.project_scanner_agent import PROJECT_SCANNER_AGENT
from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)


def main() -> None:
    """Start the Project Scanner Agent A2A server."""
    logger.info("Starting Project Scanner Agent server...")

    # Define AgentSkill
    skills = [
        AgentSkill(
            id="project_scanner",
            name="Project Scanner",
            description="Scan project structure using filesystem access.",
            examples=[
                "Scan the project structure of the current directory.",
                "Scan the project structure of the /path/to/project.",
            ],
            tags=["filesystem", "scan", "structure", "analysis"],
        )
    ]

    # Create A2A server
    a2a_app = create_agent_a2a_server(
        agent=PROJECT_SCANNER_AGENT,
        name="Project Scanner Agent",
        description="Scan project structure using filesystem access.",
        version="0.1.0",
        skills=skills,
        url=settings.project_scanner_agent_url,
    ).build()

    # Extract port from URL
    port = settings.get_port_from_url(settings.project_scanner_agent_url)

    logger.info(f"Server starting on {settings.project_scanner_agent_url}")
    logger.info(f"Binding to {settings.bind_host}:{port}")

    # Run server with Uvicorn
    uvicorn.run(
        a2a_app,
        host=settings.bind_host,
        port=port,
    )


if __name__ == "__main__":
    main()
