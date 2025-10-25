"""Type stubs for google.adk.memory.in_memory_memory_service"""

from typing import Any

class BaseMemoryService:
    """Base memory service interface."""
    ...

class InMemoryMemoryService(BaseMemoryService):
    """In-memory memory service implementation."""

    def __init__(self) -> None: ...
