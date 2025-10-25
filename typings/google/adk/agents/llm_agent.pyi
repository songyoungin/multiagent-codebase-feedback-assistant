"""Type stubs for google.adk.agents.llm_agent"""

from typing import Any

from google.adk.agents.base_agent import BaseAgent

class LlmAgent(BaseAgent):
    """LLM-based Agent."""

    def __init__(self, **data: Any) -> None: ...
