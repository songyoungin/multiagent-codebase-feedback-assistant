"""Dependency Checker Agent definition."""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool

from common.logger import get_logger
from common.prompts import DEPENDENCY_CHECKER_PROMPT
from common.settings import settings
from tools.dependency_checker_tool import check_unused_dependencies

logger = get_logger(__name__)

# Create function tool for dependency checking
CHECK_DEPENDENCIES_TOOL = FunctionTool(func=check_unused_dependencies)

# Create LLM model with automatic tool selection
CHECKER_MODEL = LiteLlm(model=settings.default_model, tool_choice="auto")

# Create agent with model, prompt, and tools
DEPENDENCY_CHECKER_AGENT = LlmAgent(
    name="dependency_checker_agent",
    model=CHECKER_MODEL,
    instruction=DEPENDENCY_CHECKER_PROMPT,
    tools=[CHECK_DEPENDENCIES_TOOL],
)

logger.info("Dependency Checker Agent initialized successfully")
