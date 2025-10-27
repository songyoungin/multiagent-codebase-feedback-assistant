"""A2A server for documentation generator agent."""

import uvicorn
from a2a.types import AgentSkill

from agents.documentation_generator.documentation_generator_agent import DOCUMENTATION_GENERATOR_AGENT
from agents.helpers.create_a2a_server import create_agent_a2a_server
from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)


def main() -> None:
    """Start the Documentation Generator Agent A2A server."""
    logger.info("Starting Documentation Generator Agent server...")

    # Define AgentSkill
    skills = [
        AgentSkill(
            id="documentation_generator",
            name="Documentation Generator",
            description="Analyze Python code documentation and identify missing docstrings.",
            examples=[
                "Analyze documentation coverage in the current project.",
                "Find missing docstrings in /path/to/project.",
                "Generate docstring suggestions for undocumented functions.",
            ],
            tags=["documentation", "docstrings", "analysis", "code-quality"],
        )
    ]

    # Create A2A server
    a2a_app = create_agent_a2a_server(
        agent=DOCUMENTATION_GENERATOR_AGENT,
        name="Documentation Generator Agent",
        description="Analyze Python code documentation and identify missing docstrings.",
        version="0.1.0",
        skills=skills,
        url=settings.documentation_generator_agent_url,
    ).build()

    # Extract port from URL
    port = settings.get_port_from_url(settings.documentation_generator_agent_url)

    logger.info(f"Server starting on {settings.documentation_generator_agent_url}")
    logger.info(f"Binding to {settings.bind_host}:{port}")

    # Run server with Uvicorn
    uvicorn.run(
        a2a_app,
        host=settings.bind_host,
        port=port,
    )


if __name__ == "__main__":
    main()
