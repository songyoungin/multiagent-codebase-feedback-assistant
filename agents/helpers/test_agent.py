"""Helper utilities for running agents locally without A2A server."""

from uuid import uuid4

from google.adk import Agent
from google.adk.agents.run_config import RunConfig
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from common.logger import get_logger

logger = get_logger(__name__)


async def run_agent_locally(agent: Agent, message: str) -> None:
    """Run an agent locally with a direct message (no A2A server required).

    Args:
        agent: Agent instance to run
        message: User message to send to the agent
    """
    logger.info("Sending message to agent: %s", message)

    # Create runner with in-memory services
    runner: Runner = Runner(
        app_name="agents",
        agent=agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

    # Generate IDs for session
    user_id = "test_user"
    session_id = str(uuid4())

    # Create message content
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    # Run agent and collect events
    logger.info("\n" + "=" * 80)
    logger.info("Agent response:")
    logger.info("=" * 80)

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
        run_config=RunConfig(max_llm_calls=5),
    ):
        # Print agent response events
        if hasattr(event, "content") and event.content:
            parts = event.content.parts
            if parts is not None:
                for part in parts:
                    if hasattr(part, "text") and part.text:
                        logger.info(part.text)

    logger.info("=" * 80 + "\n")

    # Close runner
    await runner.close()
