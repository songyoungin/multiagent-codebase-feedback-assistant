"""A2A server for SRP Violation Detector agent."""

import uvicorn
from a2a.types import AgentSkill

from agents.helpers.create_a2a_server import create_agent_a2a_server
from agents.srp_violation_detector.srp_violation_detector_agent import (
    SRP_VIOLATION_DETECTOR_AGENT,
)
from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)


def main() -> None:
    """Start the SRP Violation Detector Agent A2A server."""
    logger.info("Starting SRP Violation Detector Agent server...")

    # Define AgentSkill
    skills = [
        AgentSkill(
            id="srp_violation_detector",
            name="SRP Violation Detector",
            description="Detect Single Responsibility Principle violations in Python code using semantic analysis.",
            examples=[
                "Analyze SRP violations in the current project.",
                "Check for Single Responsibility Principle violations in /path/to/project.",
                "Find functions and classes with multiple responsibilities.",
            ],
            tags=["code-quality", "srp", "refactoring", "semantic-analysis"],
        )
    ]

    # Create A2A server
    a2a_app = create_agent_a2a_server(
        agent=SRP_VIOLATION_DETECTOR_AGENT,
        name="SRP Violation Detector Agent",
        description="Detect Single Responsibility Principle violations in Python code using semantic analysis.",
        version="0.1.0",
        skills=skills,
        url=settings.srp_violation_detector_agent_url,
    ).build()

    # Extract port from URL
    port = settings.get_port_from_url(settings.srp_violation_detector_agent_url)

    logger.info(f"Server starting on {settings.srp_violation_detector_agent_url}")
    logger.info(f"Binding to {settings.bind_host}:{port}")

    # Run server with Uvicorn
    uvicorn.run(
        a2a_app,
        host=settings.bind_host,
        port=port,
    )


if __name__ == "__main__":
    main()
