# Type stubs for google.adk package

from typing import Any

# Agent is actually an alias for LlmAgent
class LlmAgent:
    """LLM-based Agent."""
    name: str

    def __init__(self, **data: Any) -> None: ...

Agent = LlmAgent
