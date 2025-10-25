"""Type stubs for google.adk.sessions"""

from typing import Any

class BaseSessionService:
    """Base session service interface."""
    ...

class InMemorySessionService(BaseSessionService):
    """In-memory session service implementation."""

    def __init__(self) -> None: ...
