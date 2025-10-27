"""Documentation Generator Agent definition."""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool

from common.logger import get_logger
from common.prompts import DOCUMENTATION_GENERATOR_PROMPT
from common.settings import settings
from tools.documentation_analyzer_tool import analyze_documentation

logger = get_logger(__name__)

# Create function tool for documentation analysis
DOCUMENTATION_ANALYZER_TOOL = FunctionTool(func=analyze_documentation)

# Create LLM model with automatic tool selection
GENERATOR_MODEL = LiteLlm(model=settings.default_model, tool_choice="auto")

# Create agent with model, prompt, and tools
DOCUMENTATION_GENERATOR_AGENT = LlmAgent(
    name="documentation_generator_agent",
    model=GENERATOR_MODEL,
    instruction=DOCUMENTATION_GENERATOR_PROMPT,
    tools=[DOCUMENTATION_ANALYZER_TOOL],
)

logger.info("Documentation Generator Agent initialized successfully")
