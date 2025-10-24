"""Project Scanner Agent client entry point."""

import argparse
import asyncio
from uuid import uuid4

import httpx
from google.adk import ClientCallContext, ClientConfig, Message, RunConfig, TextPart
from google.adk.a2a import A2ACardResolver, ClientFactory

from common.logger import get_logger
from common.settings import settings

logger = get_logger(__name__)

AGENT_URL = settings.project_scanner_agent_url


async def run_scanner_agent(message: str, max_llm_calls: int = 5) -> None:
    """Send a message to the Project Scanner Agent and receive the result as streaming.

    Args:
        message: User request message
        max_llm_calls: Maximum number of LLM calls
    """
    logger.info(f"Connecting to Project Scanner Agent at {AGENT_URL}")

    async with httpx.AsyncClient(timeout=600) as httpx_client:
        try:
            # Get Agent Card
            card_resolver = A2ACardResolver(
                httpx_client=httpx_client, base_url=AGENT_URL
            )
            card = await card_resolver.get_agent_card()

            print(f"✅ Connected to: {card.name} (v{card.version})")
            print(f"📋 Description: {card.description}\n")

            # Create client
            client_config = ClientConfig(httpx_client=httpx_client, streaming=True)
            factory = ClientFactory(config=client_config)
            client = factory.create(card=card)

            # Send message
            request = Message(
                messageId=str(uuid4()), role="user", parts=[TextPart(text=message)]
            )

            context = ClientCallContext(
                run_config=RunConfig(max_llm_calls=max_llm_calls)
            )
            result = client.send_message(request, context=context)

            # Handle streaming events
            print("🔄 Streaming response:\n")
            async for ev in result:
                if ev.type == "message" and ev.message.role == "agent":
                    for part in ev.message.parts:
                        if hasattr(part, "text"):
                            print(part.text)

        except httpx.ConnectError:
            logger.error(f"Cannot connect to agent at {AGENT_URL}")
            print(f"❌ Error: Cannot connect to agent at {AGENT_URL}")
            print("Make sure the agent server is running:")
            print(
                "  uv run python -m agents.project_scanner_agent.project_scanner_server"
            )
        except Exception as e:
            logger.error(f"Error during agent communication: {e}", exc_info=True)
            print(f"❌ Error: {e}")


def main() -> None:
    """Command line interface."""
    parser = argparse.ArgumentParser(description="Project Scanner Agent Client")
    parser.add_argument(
        "--command",
        type=str,
        required=True,
        help=(
            "User request "
            "(e.g., '/Users/serena/Documents/development/private/"
            "multiagent-codebase-feedback-assistant path to scan')"
        ),
    )
    parser.add_argument(
        "--max-llm-calls", type=int, default=5, help="Maximum number of LLM calls"
    )

    args = parser.parse_args()
    asyncio.run(run_scanner_agent(args.command, args.max_llm_calls))


if __name__ == "__main__":
    main()
