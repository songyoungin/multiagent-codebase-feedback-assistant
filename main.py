"""A2A client for testing agents.

Usage:
uv run python main.py --agent-url http://localhost:8301 --command "Scan the project at /Users/serena/Documents/development/private/multiagent-codebase-feedback-assistant"
"""

import argparse
import asyncio
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientCallContext, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart

from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)

# Constants
MAX_MESSAGE_LENGTH = 2000
SEPARATOR = "-" * 80


def _extract_task_from_event(event: Any) -> Any:
    """Extract Task object from event.

    Args:
        event: Event from streaming response (can be tuple or Task)

    Returns:
        Task object
    """
    return event[0] if isinstance(event, (tuple, list)) else event


def _get_history(task: Any) -> list[Any]:
    """Get history list from Task object.

    Args:
        task: Task object

    Returns:
        List of messages in history, empty list if no history
    """
    if not hasattr(task, "history"):
        return []
    return list(getattr(task, "history", []))


def _extract_text_from_message(message: Any) -> str | None:
    """Extract text content from message parts.

    Args:
        message: Message object with parts attribute

    Returns:
        Extracted text or None if no text found
    """
    if not hasattr(message, "parts"):
        return None

    for part in message.parts:
        part_data = part.root if hasattr(part, "root") else part
        if hasattr(part_data, "text"):
            text = part_data.text
            return str(text) if text is not None else None

    return None


def _log_message(message: Any) -> None:
    """Log a single message with truncation if needed.

    Args:
        message: Message object to log
    """
    msg_str = str(message)
    truncated_msg = msg_str if len(msg_str) < MAX_MESSAGE_LENGTH else msg_str[:MAX_MESSAGE_LENGTH]
    logger.info(truncated_msg)
    logger.info(SEPARATOR)


def _log_final_message(task: Any) -> None:
    """Log the final message from task history.

    Args:
        task: Task object containing history
    """
    history = _get_history(task)
    if not history:
        return

    logger.info("Final message from agent:")

    last_message = history[-1]
    text = _extract_text_from_message(last_message)
    if text:
        logger.info(text)


async def _handle_streaming_events(result: Any) -> Any:
    """Handle streaming events and output new messages incrementally.

    Args:
        result: Async generator of streaming events

    Returns:
        Last event received
    """
    previous_history_length = 0
    last_event = None

    async for event in result:
        last_event = event
        task = _extract_task_from_event(event)
        history = _get_history(task)

        # Output only new messages
        if len(history) > previous_history_length:
            new_messages = history[previous_history_length:]
            for msg in new_messages:
                _log_message(msg)
            previous_history_length = len(history)

    return last_event


async def run_agent_client(agent_url: str, message: str) -> None:
    """Send a message to an agent and receive the result as streaming.

    Args:
        agent_url: Agent URL to connect to
        message: User request message
    """
    logger.info(f"Connecting to agent at {agent_url}")

    async with httpx.AsyncClient(timeout=600) as httpx_client:
        try:
            # Get Agent Card
            card_resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
            card = await card_resolver.get_agent_card()

            logger.info(f"✅ Connected to: {card.name} (v{card.version})")
            logger.info(f"📋 Description: {card.description}\n")

            # Create client with streaming enabled
            client_config = ClientConfig(httpx_client=httpx_client, streaming=True)
            factory = ClientFactory(config=client_config)
            client = factory.create(card=card)

            # Send message
            request = Message(
                message_id=str(uuid4()),
                role=Role.user,
                parts=[Part(TextPart(text=message))],
            )

            context = ClientCallContext()
            result = client.send_message(request, context=context)

            # Handle streaming events
            logger.info(SEPARATOR)
            last_event = await _handle_streaming_events(result)

            # Output final message
            if last_event is not None:
                task = _extract_task_from_event(last_event)
                _log_final_message(task)

        except httpx.ConnectError:
            logger.error(f"❌ Cannot connect to agent at {agent_url}")
            logger.error("Make sure the agent server is running:")
            logger.error("  Example: uv run python -m agents.project_scanner_agent.project_scanner_server")
        except Exception as e:
            logger.error(f"❌ Error during agent communication: {e}", exc_info=True)


def main() -> None:
    """Command line interface."""
    parser = argparse.ArgumentParser(description="Agent A2A Client")
    parser.add_argument(
        "--agent-url",
        type=str,
        default=settings.project_scanner_agent_url,
        help="Agent URL to connect to (default: project scanner agent from settings)",
    )
    parser.add_argument(
        "--command",
        type=str,
        required=True,
        help="User request message to send to the agent",
    )

    args = parser.parse_args()
    asyncio.run(run_agent_client(args.agent_url, args.command))


if __name__ == "__main__":
    main()
