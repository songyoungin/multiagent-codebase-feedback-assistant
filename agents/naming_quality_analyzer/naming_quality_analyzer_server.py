"""A2A server for Naming Quality Analyzer agent."""

import uvicorn
from a2a.types import AgentSkill

from agents.helpers.create_a2a_server import create_agent_a2a_server
from agents.naming_quality_analyzer.naming_quality_analyzer_agent import (
    NAMING_QUALITY_ANALYZER_AGENT,
)
from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)


def main() -> None:
    """Start the Naming Quality Analyzer Agent A2A server."""
    logger.info("Starting Naming Quality Analyzer Agent server...")

    # Define AgentSkill
    skills = [
        AgentSkill(
            id="naming_quality_analyzer",
            name="Naming Quality Analyzer",
            description="Analyze naming quality in Python code using semantic understanding.",
            examples=[
                "Analyze naming quality in the current project.",
                "Check for poor variable and function names in /path/to/project.",
                "Find misleading or unclear names in my codebase.",
            ],
            tags=["code-quality", "naming", "readability", "semantic-analysis"],
        )
    ]

    # Create A2A server
    a2a_app = create_agent_a2a_server(
        agent=NAMING_QUALITY_ANALYZER_AGENT,
        name="Naming Quality Analyzer Agent",
        description="Analyze naming quality in Python code using semantic understanding.",
        version="0.1.0",
        skills=skills,
        url=settings.naming_quality_analyzer_agent_url,
    ).build()

    # Extract port from URL
    port = settings.get_port_from_url(settings.naming_quality_analyzer_agent_url)

    logger.info(f"Server starting on {settings.naming_quality_analyzer_agent_url}")
    logger.info(f"Binding to {settings.bind_host}:{port}")

    # Run server with Uvicorn
    uvicorn.run(
        a2a_app,
        host=settings.bind_host,
        port=port,
    )


if __name__ == "__main__":
    main()
