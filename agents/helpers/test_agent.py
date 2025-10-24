"""Helper utilities for running agents locally without A2A server."""

from google.adk import Agent

from common.logger import get_logger

logger = get_logger(__name__)


async def run_agent_locally(agent: Agent, message: str) -> None:
    """Run an agent locally with a direct message (no A2A server required).

    Args:
        agent: Agent instance to run
        message: User message to send to the agent
    """
    logger.info("Sending message to agent: %s", message)

    # Send message to agent
    response = await agent.send(message)

    # Print response
    logger.info("Agent response: %s", response)
