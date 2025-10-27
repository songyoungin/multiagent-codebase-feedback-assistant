"""Orchestrator Agent definition."""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

from common.logger import get_logger
from common.prompts import ORCHESTRATOR_PROMPT
from common.settings import settings

logger = get_logger(__name__)


def _build_agent_card_url(base_url: str) -> str:
    """Build agent card URL with well-known path.

    Args:
        base_url: Base URL of the agent (e.g., http://localhost:8301)

    Returns:
        Agent card URL with well-known path
    """
    normalized = base_url.rstrip("/")
    return f"{normalized}/{AGENT_CARD_WELL_KNOWN_PATH}"


# Define remote A2A agents for each specialized agent
PROJECT_SCANNER_AGENT = RemoteA2aAgent(
    name="project_scanner",
    description="Scan project directory structure, collect file and directory statistics, and analyze file type distribution.",
    agent_card=_build_agent_card_url(settings.project_scanner_agent_url),
)

DEPENDENCY_CHECKER_AGENT = RemoteA2aAgent(
    name="dependency_checker",
    description="Analyze Python project dependencies to identify unused packages by comparing declared dependencies with actual imports.",
    agent_card=_build_agent_card_url(settings.dependency_checker_agent_url),
)

DOCUMENTATION_GENERATOR_AGENT = RemoteA2aAgent(
    name="documentation_generator",
    description="Analyze Python code documentation coverage, identify missing docstrings, and prioritize documentation needs.",
    agent_card=_build_agent_card_url(settings.documentation_generator_agent_url),
)

SRP_VIOLATION_DETECTOR_AGENT = RemoteA2aAgent(
    name="srp_violation_detector",
    description="Detect Single Responsibility Principle violations in Python code through semantic analysis of functions and classes.",
    agent_card=_build_agent_card_url(settings.srp_violation_detector_agent_url),
)

NAMING_QUALITY_ANALYZER_AGENT = RemoteA2aAgent(
    name="naming_quality_analyzer",
    description="Analyze naming quality in Python code, identifying misleading names, clarity issues, and consistency problems.",
    agent_card=_build_agent_card_url(settings.naming_quality_analyzer_agent_url),
)

# Wrap agents as tools
PROJECT_SCANNER_TOOL = AgentTool(PROJECT_SCANNER_AGENT)
DEPENDENCY_CHECKER_TOOL = AgentTool(DEPENDENCY_CHECKER_AGENT)
DOCUMENTATION_GENERATOR_TOOL = AgentTool(DOCUMENTATION_GENERATOR_AGENT)
SRP_VIOLATION_DETECTOR_TOOL = AgentTool(SRP_VIOLATION_DETECTOR_AGENT)
NAMING_QUALITY_ANALYZER_TOOL = AgentTool(NAMING_QUALITY_ANALYZER_AGENT)

# Create LLM model with automatic tool selection
# Use large context model for orchestrator to handle multiple agent results
ORCHESTRATOR_MODEL = LiteLlm(model=settings.large_context_model, tool_choice="auto")

# Assemble all agent tools
AGENT_TOOLS = [
    PROJECT_SCANNER_TOOL,
    DEPENDENCY_CHECKER_TOOL,
    DOCUMENTATION_GENERATOR_TOOL,
    SRP_VIOLATION_DETECTOR_TOOL,
    NAMING_QUALITY_ANALYZER_TOOL,
]

# Create orchestrator agent with all sub-agent tools
ORCHESTRATOR_AGENT = LlmAgent(
    name="orchestrator_agent",
    model=ORCHESTRATOR_MODEL,
    instruction=ORCHESTRATOR_PROMPT,
    tools=AGENT_TOOLS,
)

logger.info("Orchestrator Agent initialized with %d sub-agent tools", len(AGENT_TOOLS))
