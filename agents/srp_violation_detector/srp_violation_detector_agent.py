"""SRP Violation Detector Agent definition."""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool

from common.logger import get_logger
from common.prompts import SRP_VIOLATION_DETECTOR_PROMPT
from common.settings import settings
from tools.srp_analyzer_tool import analyze_srp_violations

logger = get_logger(__name__)

# Create function tool for SRP analysis
SRP_ANALYZER_TOOL = FunctionTool(func=analyze_srp_violations)

# Create LLM model with automatic tool selection (use large context model for code analysis)
DETECTOR_MODEL = LiteLlm(model=settings.large_context_model, tool_choice="auto")

# Create agent with model, prompt, and tools
SRP_VIOLATION_DETECTOR_AGENT = LlmAgent(
    name="srp_violation_detector_agent",
    model=DETECTOR_MODEL,
    instruction=SRP_VIOLATION_DETECTOR_PROMPT,
    tools=[SRP_ANALYZER_TOOL],
)

logger.info("SRP Violation Detector Agent initialized successfully")
