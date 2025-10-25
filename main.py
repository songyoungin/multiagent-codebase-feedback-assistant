"""A2A client for testing agents.

Usage:
uv run python main.py --agent-url http://localhost:8301 --command "Scan the project at /Users/serena/Documents/development/private/multiagent-codebase-feedback-assistant"
"""

import argparse
import asyncio
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientCallContext, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart

from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)


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

            # Create client
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
            logger.info("🔄 Streaming response:\n")
            async for ev in result:
                # ev is a union type of tuple[Task, ...] | Message
                if isinstance(ev, Message):
                    if ev.role == "agent":
                        for part in ev.parts:
                            # Part is RootModel[Union[TextPart, FilePart, DataPart]]
                            part_data = part.root if hasattr(part, "root") else part
                            if hasattr(part_data, "text"):
                                logger.info(part_data.text)

        except httpx.ConnectError:
            logger.error(f"Cannot connect to agent at {agent_url}")
            logger.error(f"❌ Error: Cannot connect to agent at {agent_url}")
            logger.error("Make sure the agent server is running:")
            logger.error("  Example: uv run python -m agents.project_scanner_agent.project_scanner_server")
        except Exception as e:
            logger.error(f"Error during agent communication: {e}", exc_info=True)
            logger.error(f"❌ Error: {e}")


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
