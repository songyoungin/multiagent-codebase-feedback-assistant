"""Naming Quality Analyzer Agent definition."""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool

from common.logger import get_logger
from common.prompts import NAMING_QUALITY_ANALYZER_PROMPT
from common.settings import settings
from tools.naming_analyzer_tool import analyze_naming_quality

logger = get_logger(__name__)

# Create function tool for naming quality analysis
NAMING_ANALYZER_TOOL = FunctionTool(func=analyze_naming_quality)

# Create LLM model with automatic tool selection
ANALYZER_MODEL = LiteLlm(model=settings.default_model, tool_choice="auto")

# Create agent with model, prompt, and tools
NAMING_QUALITY_ANALYZER_AGENT = LlmAgent(
    name="naming_quality_analyzer_agent",
    model=ANALYZER_MODEL,
    instruction=NAMING_QUALITY_ANALYZER_PROMPT,
    tools=[NAMING_ANALYZER_TOOL],
)

logger.info("Naming Quality Analyzer Agent initialized successfully")
