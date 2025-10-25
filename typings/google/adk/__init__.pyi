# Type stubs for google.adk package

from typing import Any

# Agent는 실제로 LlmAgent를 가리킴
class LlmAgent:
    """LLM-based Agent."""
    name: str

    def __init__(self, **data: Any) -> None: ...

Agent = LlmAgent
