"""Project Scanner Agent definition."""

import asyncio

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool

from agents.helpers.test_agent import run_agent_locally
from common.logger import get_logger
from common.prompts import PROJECT_SCANNER_PROMPT
from common.settings import settings
from tools.filesystem_tool import scan_project

logger = get_logger(__name__)

# Create function tool for project scanning
SCAN_PROJECT_TOOL = FunctionTool(func=scan_project)

# Create LLM model with automatic tool selection
SCANNER_MODEL = LiteLlm(model=settings.openai_model, tool_choice="auto")

# Create agent with model, prompt, and tools
PROJECT_SCANNER_AGENT = LlmAgent(
    name="project_scanner_agent",
    model=SCANNER_MODEL,
    instruction=PROJECT_SCANNER_PROMPT,
    tools=[SCAN_PROJECT_TOOL],
)

logger.info("Project Scanner Agent initialized successfully")


if __name__ == "__main__":
    # Run the agent locally without A2A server
    test_message = "Scan the project at /Users/serena/Documents/development/private/multiagent-codebase-feedback-assistant"
    asyncio.run(run_agent_locally(PROJECT_SCANNER_AGENT, test_message))
